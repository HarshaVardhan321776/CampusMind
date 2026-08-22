import os
import re
import chromadb
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import get_embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models available (fast & verified)
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3.6-27b"
]

STOPWORDS = {
    "what", "is", "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "how", "do", "does", "did", "can", "could", "would", "should", "will", "are", "were",
    "was", "be", "been", "being", "have", "has", "had", "with", "by", "from", "about",
    "into", "through", "during", "before", "after", "above", "below", "up", "down", "out",
    "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "tell", "me", "explain", "describe", "write", "give", "example", "examples", "please",
    "i", "my", "we", "our", "you", "your", "they", "their", "it", "its", "this", "that"
}


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=CHROMA_DIR,
    )


def clean_model_output(text: str) -> str:
    """Strip internal reasoning tags e.g. <think>...</think> from models like Qwen."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>[\s\S]*?<\/think>", "", text).strip()
    return cleaned


def retrieve_hybrid_context(
    question: str,
    user_id: int | None = None,
    document_id: int | None = None,
) -> tuple[list[dict], list[str]]:
    """
    High-Precision Hybrid Retrieval Pipeline:
    1. Extracts non-stopword domain keywords from question.
    2. Enforces strict user & document scoping in ChromaDB.
    3. Retrieves candidate vector matches.
    4. Performs exact keyword and lexical scanning across user's chunks (Exact Content Fallback).
    5. Calculates composite lexical + exact-match + document-affinity + vector scores.
    6. Penalizes/discards cross-topic irrelevant chunks (e.g. Git sheet for Python questions).
    7. Applies strict relevance threshold.
    Returns: (list of accepted chunk dicts, list of verified source names).
    """
    if user_id is None:
        return [], []

    where_filter = {"user_id": int(user_id)}
    if document_id is not None:
        where_filter = {"$and": [{"user_id": int(user_id)}, {"document_id": int(document_id)}]}

    # Extract non-stopword query keywords
    raw_tokens = re.findall(r"\b\w+\b", question.lower())
    query_terms = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]
    normalized_q = " ".join(query_terms)

    # 1. Fetch user chunks directly from ChromaDB
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = chroma_client.get_collection(COLLECTION_NAME)
        user_records = collection.get(where=where_filter, include=["documents", "metadatas"])
    except Exception as e:
        print(f"[Chroma Retrieval Error]: {e}")
        return [], []

    if not user_records or not user_records.get("documents"):
        return [], []

    doc_texts = user_records["documents"]
    doc_metas = user_records["metadatas"]
    num_chunks = len(doc_texts)

    # 2. Perform Vector Similarity Search
    vector_scores = {}
    try:
        vectorstore = get_vectorstore()
        vec_matches = vectorstore.similarity_search_with_score(question, k=min(15, num_chunks), filter=where_filter)
        for doc_obj, distance in vec_matches:
            src = doc_obj.metadata.get("source") or doc_obj.metadata.get("document_name") or ""
            pg = str(doc_obj.metadata.get("page", ""))
            key = f"{src}_{pg}_{doc_obj.page_content[:50]}"
            vector_scores[key] = max(0.0, 1.0 - (distance / 2.0))
    except Exception as e:
        print(f"[Vector Search Fallback Warning]: {e}")

    # 3. Score all user chunks using Hybrid Lexical + Exact + Doc-Affinity + Vector metrics
    scored_candidates = []

    for text, meta in zip(doc_texts, doc_metas):
        text_lower = text.lower()
        src_name = meta.get("source") or meta.get("document_name") or "Document"
        src_lower = src_name.lower()
        page_num = meta.get("page")

        # Lexical term overlap
        if query_terms:
            matched_terms = [t for t in query_terms if t in text_lower]
            s_lex = len(matched_terms) / len(query_terms)
        else:
            s_lex = 0.0

        # Exact phrase and sub-phrase matching (Exact Content Fallback)
        s_exact = 0.0
        if len(query_terms) > 1 and normalized_q in text_lower:
            s_exact = 1.0
        elif len(query_terms) > 1 and any(f"{query_terms[j]} {query_terms[j+1]}" in text_lower for j in range(len(query_terms)-1)):
            s_exact = 0.6
        elif any(t in text_lower for t in query_terms):
            s_exact = 0.25

        # Document filename affinity (e.g. "python" in "Python_Handbook.pdf")
        if query_terms:
            doc_term_matches = [t for t in query_terms if t in src_lower]
            s_doc = len(doc_term_matches) / len(query_terms)
        else:
            s_doc = 0.0

        # Vector score
        key = f"{src_name}_{str(page_num)}_{text[:50]}"
        s_vec = vector_scores.get(key, 0.0)

        # Composite score
        # Priority: Lexical overlap (45%), Exact phrase (30%), Document relevance (15%), Vector score (10%)
        total_score = (0.45 * s_lex) + (0.30 * s_exact) + (0.15 * s_doc) + (0.10 * s_vec)

        if total_score > 0.05:
            scored_candidates.append({
                "score": total_score,
                "s_lex": s_lex,
                "s_doc": s_doc,
                "text": text,
                "source": src_name,
                "page": page_num,
                "metadata": meta,
            })

    if not scored_candidates:
        return [], []

    # Sort descending by hybrid score
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    # 4. Cross-Document Noise Suppression
    top_score = scored_candidates[0]["score"]
    
    # Calculate best score per document
    best_per_doc = {}
    for c in scored_candidates:
        src = c["source"]
        if src not in best_per_doc or c["score"] > best_per_doc[src]:
            best_per_doc[src] = c["score"]

    # Minimum relevance threshold (documented threshold: 0.16)
    RELEVANCE_THRESHOLD = 0.16

    # If top score is below threshold, no document is sufficiently relevant
    if top_score < RELEVANCE_THRESHOLD:
        return [], []

    # Keep documents matching top domain score (eliminates unrelated topic bleed)
    valid_sources = {
        src for src, best_s in best_per_doc.items()
        if best_s >= RELEVANCE_THRESHOLD and best_s >= (top_score * 0.45)
    }

    accepted_chunks = []
    accepted_sources = []

    for c in scored_candidates:
        if c["source"] in valid_sources and c["score"] >= RELEVANCE_THRESHOLD:
            accepted_chunks.append(c)
            if c["source"] not in accepted_sources:
                accepted_sources.append(c["source"])
            if len(accepted_chunks) >= 5:
                break

    return accepted_chunks, accepted_sources


def answer_question(
    question: str,
    user_id: int | None = None,
    document_id: int | None = None,
    chat_history: list[dict] | None = None,
) -> dict:
    accepted_chunks, sources = retrieve_hybrid_context(
        question=question,
        user_id=user_id,
        document_id=document_id,
    )

    context_blocks = []
    if accepted_chunks:
        for i, chunk in enumerate(accepted_chunks):
            source_name = chunk["source"]
            page_num = chunk["page"]
            page_info = f" (Page {page_num})" if page_num else ""
            context_blocks.append(f"[Excerpt {i+1} from {source_name}{page_info}]\n{chunk['text'].strip()}")

    if context_blocks:
        context_text = "\n\n".join(context_blocks)
        system_prompt = (
            "You are CampusMind, an expert, encouraging, and highly intelligent academic co-pilot and campus AI assistant.\n\n"
            "Core Directives:\n"
            "1. Grounded Academic Answers: Thoroughly and clearly answer the student's question, integrating the specific definitions, formulas, rules, and code snippets from the provided document excerpts.\n"
            "2. Source Transparency: Reference the specific source document names (and page numbers where available) in your response.\n"
            "3. Comprehensive Explanations: Provide well-structured explanations using markdown headings, bullet points, numbered steps, comparison tables, or syntax-highlighted code blocks.\n"
            "4. Handwritten & OCR Notes: If excerpts contain OCR artifacts from handwritten/scanned notes, interpret the intended academic meaning accurately.\n"
            "5. Strict Relevance: Focus on the student's question and relevant excerpts. Do not bring in unrelated topics from other subjects."
        )
        user_content = f"Document Excerpts:\n{context_text}\n\nStudent Question: {question}"
    else:
        system_prompt = (
            "You are CampusMind, an expert, encouraging, and highly intelligent academic co-pilot and campus AI assistant.\n\n"
            "Core Directives:\n"
            "1. Comprehensive Academic Answers: ALWAYS provide a complete, clear, and comprehensive answer to the student's question. Explain concepts thoroughly with structured explanations, code examples, formulas, or step-by-step breakdowns.\n"
            "2. Educational Clarity: Structure your response with clean markdown headings, bullet points, comparison tables, and syntax-highlighted code blocks.\n"
            "3. Encouraging Tone: Be welcoming, articulate, and supportive of the student's learning journey.\n"
            "4. Course Context Note: If the question appears to seek specific university/course policies (e.g. syllabus cutoff, attendance requirements), provide the general standard and kindly remind the student that they can upload their course PDF to get exact campus-specific rules."
        )
        user_content = f"Student Question: {question}"

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history[-6:])

    messages.append({
        "role": "user",
        "content": user_content,
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
