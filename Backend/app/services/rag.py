import os
import re
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models available
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "qwen/qwen3.6-27b"
]


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=CHROMA_DIR,
    )


def clean_model_output(text: str) -> str:
    """Strip internal reasoning tags e.g. <think>...</think> from models like Qwen."""
    if not text:
        return ""
    # Remove <think>...</think> tags and their contents
    cleaned = re.sub(r"<think>[\s\S]*?<\/think>", "", text).strip()
    return cleaned


def answer_question(
    question: str,
    user_id: int | None = None,
    document_id: int | None = None,
    chat_history: list[dict] | None = None,
) -> dict:
    vectorstore = get_vectorstore()

    # Build Chroma filter query
    where_filter = None
    if user_id is not None and document_id is not None:
        where_filter = {"$and": [{"user_id": int(user_id)}, {"document_id": int(document_id)}]}
    elif user_id is not None:
        where_filter = {"user_id": int(user_id)}
    elif document_id is not None:
        where_filter = {"document_id": int(document_id)}

    # Retrieve top relevant context chunks with filtering
    results = []
    try:
        if where_filter:
            results = vectorstore.similarity_search(question, k=6, filter=where_filter)
        else:
            results = vectorstore.similarity_search(question, k=6)
    except Exception as e:
        print(f"[RAG Vector Search Error]: {e}")
        try:
            results = vectorstore.similarity_search(question, k=6)
        except Exception:
            results = []

    if not results:
        target_doc_msg = " in the selected document" if document_id else ""
        return {
            "answer": f"I couldn't find anything relevant{target_doc_msg} to answer your question. Please ensure the relevant document is uploaded in your Knowledge Base.",
            "sources": [],
        }

    context_blocks = []
    sources = []
    for i, doc in enumerate(results):
        source_name = doc.metadata.get("source") or doc.metadata.get("document_name") or "Document"
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
            raw_answer = completion.choices[0].message.content
            if raw_answer:
                answer = clean_model_output(raw_answer)
                if answer:
                    break
        except Exception as e:
            print(f"[Groq Model {model_name} Error]: {e}")
            last_error = e

    if not answer:
        answer = f"Sorry, I encountered an issue communicating with the AI model: {str(last_error)}"

    return {"answer": answer, "sources": sources}