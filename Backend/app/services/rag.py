import os
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import get_embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models available
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound"
]


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=CHROMA_DIR,
    )


def answer_question(question: str, chat_history: list[dict] | None = None) -> dict:
    vectorstore = get_vectorstore()
    
    # Retrieve top relevant context chunks
    try:
        results = vectorstore.similarity_search(question, k=6)
    except Exception as e:
        print(f"[RAG Vector Search Error]: {e}")
        results = []

    if not results:
        return {
            "answer": "I couldn't find anything relevant in the uploaded documents to answer that. Please ensure relevant documents are uploaded in the Knowledge Base.",
            "sources": [],
        }

    context_blocks = []
    sources = []
    for i, doc in enumerate(results):
        source_name = doc.metadata.get("source", "Document")
        page_num = doc.metadata.get("page")
        page_info = f" (Page {page_num})" if page_num else ""
        
        context_blocks.append(f"[Excerpt {i+1} from {source_name}{page_info}]\n{doc.page_content.strip()}")
        if source_name not in sources:
            sources.append(source_name)

    context_text = "\n\n".join(context_blocks)

    system_prompt = (
        "You are CampusMind, an expert, encouraging, and highly intelligent academic co-pilot and campus AI assistant. "
        "Your task is to answer the student's question accurately, thoroughly, and helpfully using the provided document excerpts. "
        "Guidelines:\n"
        "1. Ground your explanation clearly in the provided excerpts.\n"
        "2. Provide structured, readable explanations using bullet points, numbered steps, or markdown code blocks where appropriate.\n"
        "3. If the excerpts cover the topic (e.g. operators, variables, policies, formulas), provide a comprehensive and easy-to-understand explanation based on the material.\n"
        "4. If the excerpt text contains slight OCR typos from handwritten/scanned notes, interpret the intended academic meaning accurately.\n"
        "5. If the provided excerpts genuinely contain zero relevant information about the question, politely explain what topics were found in the document and that the specific query was not found in the current excerpts.\n"
        "6. Mention which source document(s) you consulted."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        # Keep last 6 messages to preserve context without exceeding token limits
        messages.extend(chat_history[-6:])

    messages.append({
        "role": "user",
        "content": f"Document Excerpts:\n{context_text}\n\nStudent Question: {question}",
    })

    # Call LLM with fallback
    answer = None
    last_error = None
    for model_name in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
            answer = completion.choices[0].message.content
            if answer:
                break
        except Exception as e:
            print(f"[Groq Model {model_name} Error]: {e}")
            last_error = e

    if not answer:
        answer = f"Sorry, I encountered an issue communicating with the AI model: {str(last_error)}"

    return {"answer": answer, "sources": sources}
