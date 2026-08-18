from groq import Groq
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.embeddings import embedding_function, CHROMA_DIR, COLLECTION_NAME

client = Groq(api_key=settings.GROQ_API_KEY)


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=CHROMA_DIR,
    )


def answer_question(question: str, chat_history: list[dict] | None = None) -> dict:
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(question, k=4)

    if not results:
        return {
            "answer": "I couldn't find anything relevant in the uploaded documents to answer that.",
            "sources": [],
        }

    context_blocks = []
    sources = []
    for i, doc in enumerate(results):
        source_name = doc.metadata.get("source", "Unknown")
        context_blocks.append(f"[Source {i+1}: {source_name}]\n{doc.page_content}")
        if source_name not in sources:
            sources.append(source_name)

    context_text = "\n\n".join(context_blocks)

    system_prompt = (
        "You are CampusMind, a helpful assistant that answers student questions "
        "using ONLY the provided document excerpts. "
        "If the answer isn't in the excerpts, say you don't have that information. "
        "Always mention which source(s) you used."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {question}",
    })

    completion = client.chat.completions.create(
      model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.2,
    )

    answer = completion.choices[0].message.content

    return {"answer": answer, "sources": sources}