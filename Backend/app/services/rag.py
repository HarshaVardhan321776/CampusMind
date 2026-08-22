import os
import re
import chromadb
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import get_embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models available (fast & high quota)
GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound-mini",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-safeguard-20b"
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
    "i", "my", "we", "our", "you", "your", "they", "their", "it", "its", "this", "that",
    "matter", "find", "show", "use", "using", "used", "make", "get", "need", "know", "see"
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

    # Aggregate & transcript query keywords requiring complete document context
    AGGREGATE_TERMS = {
        "cgpa", "sgpa", "gpa", "grade", "grades", "mark", "marks", "marksheet",
        "transcript", "credit", "credits", "semester", "sem", "calculate",
        "summary", "breakdown", "all courses", "all subjects", "percentage",
        "performance", "exam", "result", "results"
    }
    is_aggregate_query = any(t in query_terms for t in AGGREGATE_TERMS)

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

        # Lexical term overlap using whole-word boundary and stem matching
        if query_terms:
            matched_terms = []
            for t in query_terms:
                stem = t.rstrip("s") if len(t) > 3 else t
                pattern = r"\b" + re.escape(stem) + r"\w*\b"
                if re.search(pattern, text_lower):
                    matched_terms.append(t)

            if len(query_terms) >= 3 and len(matched_terms) == 1:
                s_lex = (len(matched_terms) / len(query_terms)) * 0.4
            else:
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

        # Grade Sheet & Transcript affinity boost
        if is_aggregate_query and ("grade" in src_lower or "mark" in src_lower or "exam" in text_lower or "cgpa" in text_lower or "semester" in text_lower):
            s_doc += 0.45

        # Vector score
        key = f"{src_name}_{str(page_num)}_{text[:50]}"
        s_vec = vector_scores.get(key, 0.0)

        # Composite score
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

    # Minimum relevance threshold
    RELEVANCE_THRESHOLD = 0.18

    if not best_per_doc or top_score < RELEVANCE_THRESHOLD:
        return [], []

    # Sort documents strictly by hybrid score descending
    sorted_doc_tuples = sorted(best_per_doc.items(), key=lambda x: x[1], reverse=True)
    top_doc_score = sorted_doc_tuples[0][1]

    # Keep only the top-matching document(s) (>= 80% of top document score)
    primary_sources = [
        src for src, s in sorted_doc_tuples
        if s >= RELEVANCE_THRESHOLD and s >= (top_doc_score * 0.80)
    ]

    accepted_chunks = []
    accepted_sources = []

    # For aggregate queries or short documents, extract pages for the top document first in page order
    if is_aggregate_query or len(doc_texts) <= 8:
        for target_src in primary_sources:
            doc_chunks = []
            for text, meta in zip(doc_texts, doc_metas):
                src = meta.get("source") or meta.get("document_name") or "Document"
                if src == target_src:
                    doc_chunks.append({
                        "score": best_per_doc[src],
                        "text": text,
                        "source": src,
                        "page": meta.get("page", 1),
                        "metadata": meta,
                    })
            # Sort chronologically by page number
            doc_chunks.sort(key=lambda x: int(x.get("page") or 1))
            for chk in doc_chunks:
                accepted_chunks.append(chk)
                if target_src not in accepted_sources:
                    accepted_sources.append(target_src)
                if len(accepted_chunks) >= 8:
                    break
            if len(accepted_chunks) >= 8:
                break
    else:
        for c in scored_candidates:
            if c["source"] in primary_sources and c["score"] >= RELEVANCE_THRESHOLD:
                accepted_chunks.append(c)
                if c["source"] not in accepted_sources:
                    accepted_sources.append(c["source"])
                if len(accepted_chunks) >= 6:
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
            "You are CampusMind, a friendly, direct, and ultra-clear academic AI co-pilot for college students.\n\n"
            "Communication Style:\n"
            "- Direct & Simple: Always put the direct answer and key figures at the very top. Speak in clear, natural, everyday English that is effortless to read.\n"
            "- No Jargon / No Fake Examples: NEVER invent fictional courses (like Math 101) or give generic textbook lectures when student documents are provided.\n"
            "- Clean Formatting: Use clean markdown tables, bold numbers, and bullet points. Never write messy raw LaTeX formulas like [ \\text{GPA} = ... ].\n\n"
            "Grade Sheets & Transcripts:\n"
            "1. Official CGPA First: State the official printed CGPA immediately at the top in bold (e.g. '**Your CGPA: 7.77**').\n"
            "2. Summary Table: Provide a clean, compact Semester-wise SGPA summary table.\n"
            "3. Detailed Course Breakdown: Show each semester with exact subject codes, course titles, credits, grades, and grade points from the document.\n\n"
            "Study Notes & Technical Concepts:\n"
            "1. Plain-English Explanation: Explain the concept in 2-3 clear, simple sentences.\n"
            "2. Clean Code / Example: Provide a short, practical code snippet with comments if relevant.\n"
            "3. Key Takeaway: Give a 1-sentence bottom line."
        )
        user_content = f"Document Excerpts:\n{context_text}\n\nStudent Question: {question}"
    else:
        system_prompt = (
            "You are CampusMind, a friendly, direct, and ultra-clear academic AI co-pilot for college students.\n\n"
            "Communication Directives:\n"
            "1. Simple, Direct & Conversational: Answer directly in simple, clear, everyday English. Avoid dense robotic textbook lectures or raw LaTeX math code.\n"
            "2. No Code Unless Requested: Do NOT provide programming code blocks (like Python scripts) unless the student explicitly asks for code or programming solutions.\n"
            "3. Clear Step-by-Step Guidance: When explaining academic concepts or formulas (like CGPA/SGPA calculation), explain the steps in simple words with a practical real-world example.\n"
            "4. Upload Tip: If the question is about university marks or policies, kindly mention that uploading their grade sheet or syllabus PDF will allow exact automatic calculation."
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
                max_tokens=2500,
                timeout=25.0
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
