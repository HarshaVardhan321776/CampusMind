import os
import re
import hashlib
import chromadb
from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import get_embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)

# Primary & Fallback Groq models (safeguard model excluded — 8k TPM cap on free tier)
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound-mini",
]

# Groq on-demand tier allows ~8000 tokens total per request (input + max_output).
GROQ_TOTAL_TOKEN_BUDGET = 7500
DEFAULT_MAX_OUTPUT_TOKENS = 4096

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


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict]) -> int:
    return sum(estimate_tokens(m.get("content") or "") for m in messages) + (len(messages) * 4)


def trim_document_context(context_text: str, max_chars: int) -> str:
    if len(context_text) <= max_chars:
        return context_text
    return (
        context_text[:max_chars]
        + "\n\n[... additional document context omitted to fit model limits ...]"
    )


def fit_messages_to_budget(
    messages: list[dict],
    max_output_tokens: int,
) -> tuple[list[dict], int]:
    """
    Trim chat history and document context so input + max_output stays within
    Groq on-demand token budget. Returns (fitted messages, adjusted max_output).
    """
    input_budget = GROQ_TOTAL_TOKEN_BUDGET - max_output_tokens
    fitted = [dict(m) for m in messages]

    def total_input_tokens() -> int:
        return estimate_messages_tokens(fitted)

    # 1. Trim document excerpts in the last user message
    if fitted and fitted[-1].get("role") == "user":
        user_msg = fitted[-1]
        content = user_msg["content"]
        marker = "Document Excerpts:\n"
        if marker in content:
            prefix, rest = content.split(marker, 1)
            question_part = ""
            if "\n\nStudent Question: " in rest:
                doc_part, question_part = rest.split("\n\nStudent Question: ", 1)
                question_part = "\n\nStudent Question: " + question_part
            else:
                doc_part = rest

            while total_input_tokens() > input_budget and len(doc_part) > 500:
                doc_part = trim_document_context(doc_part, int(len(doc_part) * 0.75))
                user_msg["content"] = f"{prefix}{marker}{doc_part}{question_part}"

    # 2. Drop oldest history turns (keep system + current user)
    while total_input_tokens() > input_budget and len(fitted) > 2:
        # Remove first non-system message
        for i, m in enumerate(fitted):
            if m.get("role") != "system":
                fitted.pop(i)
                break

    # 3. Shorten remaining history messages
    for m in fitted[:-1]:
        content = m.get("content") or ""
        if len(content) > 1500:
            m["content"] = content[:1500] + "..."

    # 4. If still over budget, shrink max_output
    adjusted_output = max_output_tokens
    while total_input_tokens() + adjusted_output > GROQ_TOTAL_TOKEN_BUDGET and adjusted_output > 1024:
        adjusted_output -= 512

    return fitted, adjusted_output


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=CHROMA_DIR,
    )


def clean_model_output(text: str) -> str:
    """Strip internal reasoning tags and planning preambles from model responses."""
    if not text:
        return ""
    cleaned = text
    # Strip common model reasoning/thinking blocks (qwen, groq, etc.)
    tag = "think"
    cleaned = re.sub(
        rf"<(?:{tag}|redacted_thinking|reasoning)>[\s\S]*?</(?:{tag}|redacted_thinking|reasoning)>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    # Strip conversational meta-commentary preambles
    cleaned = re.sub(
        r"^(?:Sure!?|Certainly!?|Here is|Below is|I will|Let me|I'll format)[^\n]*\n+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned


def _chunk_key(source: str, page, text: str) -> str:
    """Stable lookup key for matching vector hits back to stored chunks."""
    page_str = str(page) if page is not None else ""
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
    return f"{source}|{page_str}|{text_hash}"


def compute_transcript_summary(text: str) -> str:
    """Parse exam mark details and pre-calculate exact verified SGPA and CGPA metrics."""
    if "exam mark details" not in text.lower() and "cgpa" not in text.lower():
        return ""

    sem_blocks = re.split(r"Semester\s*(\d+)", text, flags=re.IGNORECASE)
    if len(sem_blocks) < 3:
        return ""

    sem_summaries = []
    total_cum_credits = 0.0
    total_cum_points = 0.0

    cgpa_match = re.search(r"CGPA\s*[:=]\s*([\d\.]+)", text, re.IGNORECASE)
    official_cgpa = cgpa_match.group(1) if cgpa_match else None

    for i in range(1, len(sem_blocks), 2):
        sem_num = sem_blocks[i]
        block_text = sem_blocks[i+1]

        tot_credits = 0.0
        tot_points = 0.0

        pattern = r"([A-Z]{2,4}\s*\d{3}[A-Z]?)\s+([A-Za-z0-9\s,\-\/&]+?)\s+(\d+(?:\.\d+)?|-)\s+([A-O\+\-]+)\s+(\d+(?:\.\d+)?|-)"
        for m in re.finditer(pattern, block_text):
            cr_str = m.group(3).strip()
            pts_str = m.group(5).strip()
            if cr_str != "-" and pts_str != "-":
                try:
                    cr = float(cr_str)
                    pts = float(pts_str)
                    tot_credits += cr
                    tot_points += (cr * pts)
                except ValueError:
                    pass

        if tot_credits > 0:
            sgpa = round(tot_points / tot_credits, 2)
            total_cum_credits += tot_credits
            total_cum_points += tot_points
            sem_summaries.append(f"- Semester {sem_num}: Total Credits = {int(tot_credits)}, Total Points = {tot_points:.2f}, SGPA = {sgpa:.2f}")

    if not sem_summaries:
        return ""

    calculated_cgpa = round(total_cum_points / total_cum_credits, 2) if total_cum_credits > 0 else 0.0
    final_cgpa = official_cgpa if official_cgpa else f"{calculated_cgpa:.2f}"

    summary_lines = [
        "[Verified Transcript Pre-Calculations]",
        f"- Official CGPA: {final_cgpa}"
    ]
    summary_lines.extend(sem_summaries)
    summary_lines.append(f"- Overall Cumulative: Total Credits = {int(total_cum_credits)}, Total Points = {total_cum_points:.2f}, CGPA = {final_cgpa}")
    return "\n".join(summary_lines)


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

    # Domain routing keywords
    GRADE_TERMS = {
        "cgpa", "sgpa", "spa", "gpa", "grade", "grades", "mark", "marks", "marksheet",
        "transcript", "credit", "credits", "semester", "sem", "semesters", "calculate",
        "summary", "breakdown", "all courses", "all subjects", "percentage",
        "performance", "exam", "result", "results", "passed", "failed", "srm"
    }
    PYTHON_TERMS = {"python", "pip", "django", "flask", "numpy", "pandas", "def", "class", "list", "dict", "tuple", "lambda"}
    GIT_TERMS = {"git", "github", "branch", "commit", "checkout", "merge", "stash", "rebase", "repo", "pull", "push"}

    is_grade_query = any(t in query_terms for t in GRADE_TERMS)
    is_py_query = any(t in query_terms for t in PYTHON_TERMS)
    is_git_query = any(t in query_terms for t in GIT_TERMS)
    is_aggregate_query = is_grade_query

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
        vec_matches = vectorstore.similarity_search_with_score(question, k=min(25, num_chunks), filter=where_filter)
        for doc_obj, distance in vec_matches:
            src = doc_obj.metadata.get("source") or doc_obj.metadata.get("document_name") or ""
            pg = doc_obj.metadata.get("page", "")
            key = _chunk_key(src, pg, doc_obj.page_content)
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

        # Domain routing affinity scoring
        is_grade_doc = any(k in src_lower for k in ["grade", "mark", "transcript", "result", "exam"]) or ("cgpa" in text_lower or "exam mark details" in text_lower)
        is_py_doc = "python" in src_lower
        is_git_doc = "git" in src_lower

        domain_boost = 0.0
        if is_grade_query:
            if is_grade_doc:
                domain_boost = 1.5
            else:
                domain_boost = -0.5
        elif is_py_query:
            if is_py_doc:
                domain_boost = 1.0
            elif is_grade_doc:
                domain_boost = -0.5
        elif is_git_query:
            if is_git_doc:
                domain_boost = 1.0
            elif is_grade_doc:
                domain_boost = -0.5

        # Vector score
        key = _chunk_key(src_name, page_num, text)
        s_vec = vector_scores.get(key, 0.0)

        # Composite score
        total_score = (0.40 * s_lex) + (0.30 * s_exact) + (0.20 * s_doc) + (0.10 * s_vec) + domain_boost

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

    # Minimum relevance threshold — soft fallback keeps search from returning nothing
    RELEVANCE_THRESHOLD = 0.12
    SOFT_FALLBACK_THRESHOLD = 0.05

    if not best_per_doc or top_score < RELEVANCE_THRESHOLD:
        if scored_candidates and top_score >= SOFT_FALLBACK_THRESHOLD:
            fallback_chunks = []
            fallback_sources = []
            for c in scored_candidates[:8]:
                fallback_chunks.append(c)
                if c["source"] not in fallback_sources:
                    fallback_sources.append(c["source"])
            return fallback_chunks, fallback_sources
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
                if len(accepted_chunks) >= 14:
                    break
            if len(accepted_chunks) >= 14:
                break
    else:
        for c in scored_candidates:
            if c["source"] in primary_sources and c["score"] >= RELEVANCE_THRESHOLD:
                accepted_chunks.append(c)
                if c["source"] not in accepted_sources:
                    accepted_sources.append(c["source"])
                if len(accepted_chunks) >= 12:
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
        raw_context = "\n\n".join(context_blocks)
        transcript_summary = compute_transcript_summary(raw_context)
        if transcript_summary:
            context_text = f"{transcript_summary}\n\n{raw_context}"
        else:
            context_text = raw_context

        system_prompt = (
            "You are CampusMind, a thorough and patient academic tutor for college students. "
            "Your goal is to help students truly UNDERSTAND — not just get a quick answer.\n\n"
            "Answer Structure (use these sections with markdown headings):\n"
            "1. **Direct Answer** — State the answer clearly in 1-2 sentences at the top.\n"
            "2. **Detailed Explanation** — Explain the concept from first principles in plain English. "
            "Cover the why, how, and when. Use multiple paragraphs as needed — never stop at 2-3 sentences.\n"
            "3. **Step-by-Step Breakdown** — Walk through the logic or process step by step when applicable.\n"
            "4. **Examples & Illustrations** — Provide concrete examples, analogies, or worked problems. "
            "For technical topics, include well-commented code snippets.\n"
            "5. **Key Points to Remember** — Bullet list of the most important takeaways.\n"
            "6. **Common Mistakes / Tips** — Mention pitfalls or study tips when relevant.\n\n"
            "Communication Rules:\n"
            "- Be comprehensive: A good answer is typically 300-800 words unless the question is trivial.\n"
            "- Ground answers in the provided document excerpts — quote or reference them when relevant.\n"
            "- NEVER invent fictional courses or data not present in the documents.\n"
            "- Use clean markdown: headings, tables, bold for key terms, bullet points.\n"
            "- Never write raw LaTeX like [ \\text{GPA} = ... ]; use plain English or simple formulas.\n"
            "- Do NOT output planning monologues (e.g. 'I will explain this step by step'). Just answer.\n\n"
            "Grade Sheets & Transcripts:\n"
            "- Begin with the official CGPA in bold (e.g. '**Your CGPA: 7.77**').\n"
            "- Provide a semester-wise SGPA summary table.\n"
            "- Show full course breakdown per semester: Code | Subject Title | Credits | Grade | Points.\n"
            "- After the tables, briefly explain what the numbers mean and how SGPA/CGPA are calculated."
        )
        user_content = f"Document Excerpts:\n{context_text}\n\nStudent Question: {question}"
    else:
        system_prompt = (
            "You are CampusMind, a thorough and patient academic tutor for college students. "
            "Your goal is to help students truly UNDERSTAND — not just get a quick answer.\n\n"
            "Answer Structure (use these sections with markdown headings):\n"
            "1. **Direct Answer** — State the answer clearly in 1-2 sentences at the top.\n"
            "2. **Detailed Explanation** — Explain from first principles in plain, conversational English. "
            "Cover the why, how, and when. Use multiple paragraphs — never give a one-line or vague answer.\n"
            "3. **Step-by-Step Breakdown** — Walk through the logic or process step by step when applicable.\n"
            "4. **Examples & Illustrations** — Provide concrete examples, analogies, or worked problems. "
            "For programming topics, include well-commented code snippets even if not explicitly requested.\n"
            "5. **Key Points to Remember** — Bullet list of the most important takeaways.\n"
            "6. **Common Mistakes / Tips** — Mention pitfalls or study tips when relevant.\n\n"
            "Communication Rules:\n"
            "- Be comprehensive: A good answer is typically 300-800 words unless the question is trivial.\n"
            "- Write in clear, everyday English — not dense textbook jargon or raw LaTeX.\n"
            "- Do NOT output internal meta-thoughts or planning commentary.\n"
            "- Use clean markdown: headings, tables, bold for key terms, bullet points.\n"
            "- If the question is about university marks or policies, mention that uploading their "
            "grade sheet or syllabus PDF will allow exact answers from their own documents."
        )
        user_content = f"Student Question: {question}"

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history[-8:])

    messages.append({
        "role": "user",
        "content": user_content,
    })

    messages, max_output_tokens = fit_messages_to_budget(messages, DEFAULT_MAX_OUTPUT_TOKENS)

    # Call LLM with fallback — keep best partial answer if all models hit token limit
    answer = None
    partial_answer = None
    last_error = None

    for model_name in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.4,
                max_tokens=max_output_tokens,
                timeout=120.0,
            )
            choice = completion.choices[0]
            raw_answer = choice.message.content

            if choice.finish_reason == "length":
                print(f"[Model Cutoff Warning]: {model_name} hit max token limit.")
                if raw_answer:
                    cleaned = clean_model_output(raw_answer)
                    if cleaned and (partial_answer is None or len(cleaned) > len(partial_answer)):
                        partial_answer = cleaned
                continue

            if raw_answer:
                answer = clean_model_output(raw_answer)
                if answer:
                    break
        except Exception as e:
            err_str = str(e).lower()
            print(f"[Groq Model {model_name} Error]: {e}")
            last_error = e
            # Retry same model with tighter budget on token-limit errors
            if "413" in err_str or "too large" in err_str or "rate_limit" in err_str:
                messages, max_output_tokens = fit_messages_to_budget(messages, max(1024, max_output_tokens // 2))
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.4,
                        max_tokens=max_output_tokens,
                        timeout=120.0,
                    )
                    choice = completion.choices[0]
                    raw_answer = choice.message.content
                    if raw_answer:
                        answer = clean_model_output(raw_answer)
                        if answer:
                            break
                except Exception as retry_e:
                    print(f"[Groq Retry {model_name} Error]: {retry_e}")
                    last_error = retry_e

    if not answer and partial_answer:
        answer = partial_answer + "\n\n---\n*Response was trimmed due to length. Ask a follow-up for more detail on any section.*"

    if not answer:
        answer = f"Sorry, I encountered an issue communicating with the AI model: {str(last_error)}"

    return {"answer": answer, "sources": sources}
