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

    # Retrieve candidate chunks with similarity scores
    scored_results = []
    try:
        if where_filter:
            scored_results = vectorstore.similarity_search_with_score(question, k=12, filter=where_filter)
        else:
            scored_results = vectorstore.similarity_search_with_score(question, k=12)
    except Exception as e:
        print(f"[RAG Vector Search Error]: {e}")
        try:
            scored_results = vectorstore.similarity_search_with_score(question, k=12)
        except Exception:
            scored_results = []

    # Semantic relevance filtering and cross-document noise suppression
    filtered_docs = []
    if scored_results:
        min_score = min(s for d, s in scored_results)
        
        # Calculate best score per document to isolate matching subject matter
        doc_best_scores = {}
        for doc, score in scored_results:
            src = doc.metadata.get("source") or doc.metadata.get("document_name") or "doc"
            if src not in doc_best_scores or score < doc_best_scores[src]:
                doc_best_scores[src] = score

        # Keep documents whose best chunk is closely aligned with top match (eliminates unrelated topic bleed)
        valid_doc_sources = {
            src for src, best_s in doc_best_scores.items()
            if best_s <= max(1.08, min_score + 0.28)
        }

        for doc, score in scored_results:
            src = doc.metadata.get("source") or doc.metadata.get("document_name") or "doc"
            if src in valid_doc_sources and score <= max(1.12, min_score + 0.32):
                filtered_docs.append(doc)
                if len(filtered_docs) >= 6:
                    break

    context_blocks = []
    sources = []
    if filtered_docs:
        for i, doc in enumerate(filtered_docs):
            source_name = doc.metadata.get("source") or doc.metadata.get("document_name") or "Document"
            page_num = doc.metadata.get("page")
            page_info = f" (Page {page_num})" if page_num else ""

            context_blocks.append(f"[Excerpt {i+1} from {source_name}{page_info}]\n{doc.page_content.strip()}")
            if source_name not in sources:
                sources.append(source_name)

    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant document excerpts found."

    system_prompt = (
        "You are CampusMind, an expert, encouraging, and highly intelligent academic co-pilot and campus AI assistant.\n\n"
        "Core Directives:\n"
        "1. Complete Academic Answers: ALWAYS provide a complete, clear, and comprehensive answer to the student's question. NEVER say 'content is not available', 'not mentioned in the text', or refuse to answer. Explain concepts thoroughly with structured explanations, code examples, formulas, or step-by-step breakdowns.\n"
        "2. Ground in Document Context: When relevant document excerpts are provided, integrate their specific definitions, examples, and rules into your explanation, and reference the source names (and page numbers if available).\n"
        "3. Cross-Document Isolation: Focus strictly on the subject matter of the student's question. Do NOT bring up unrelated topics from other documents (e.g. never mix Git commands into Python programming questions, or vice versa).\n"
        "4. Handwritten & OCR Notes: If excerpts contain OCR artifacts from handwritten notes (e.g. 'Obera tets in?y Hhon'), reconstruct and explain the intended academic concept ('Operators in Python') with perfect accuracy.\n"
        "5. General Inquiries & Greetings: If the student sends a greeting ('Hi', 'Hello') or asks a general CS/academic question without document matches, provide a warm, helpful response and solve their query completely.\n"
        "6. Formatting: Use crisp markdown with headings, bullet points, comparison tables, and syntax-highlighted code blocks."
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
                max_tokens=1200,
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