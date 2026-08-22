import os
import re
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models available (fast & verified)
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
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

    context_blocks = []
    sources = []
    if results:
        for i, doc in enumerate(results):
            source_name = doc.metadata.get("source") or doc.metadata.get("document_name") or "Document"
            page_num = doc.metadata.get("page")
            page_info = f" (Page {page_num})" if page_num else ""

            context_blocks.append(f"[Excerpt {i+1} from {source_name}{page_info}]\n{doc.page_content.strip()}")
            if source_name not in sources:
                sources.append(source_name)

    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant document excerpts found."

    system_prompt = (
        "You are CampusMind, an expert, encouraging, and highly intelligent academic co-pilot and campus AI assistant. "
        "Your mission is to help students learn effectively, understand concepts clearly, solve problems, and master their course material.\n\n"
        "Guidelines for Your Responses:\n"
        "1. Document Grounding: When document excerpts are provided, prioritize and ground your explanations directly in those materials, citing the specific source names and page numbers where available.\n"
        "2. Comprehensive & Pedagogical: Provide thorough, structured, and easy-to-understand explanations using bullet points, numbered steps, comparison tables, or clear code blocks.\n"
        "3. OCR Interpretation: If handwritten or scanned note excerpts contain OCR distortions or typos (e.g. 'Obera tets in?y Hhon'), intelligently reconstruct the intended academic meaning (e.g. 'Operators in Python') and explain it correctly.\n"
        "4. General & Conversational Queries: If the student asks a greeting (like 'Hi', 'Hello'), introduce yourself warmly as CampusMind. If they ask a general academic or programming question not covered in the excerpts, provide a high-quality, complete academic answer and guide them to upload relevant notes in the Knowledge Base for syllabus-tailored assistance.\n"
        "5. Tone: Professional, supportive, and academically rigorous."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
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
                timeout=12.0
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