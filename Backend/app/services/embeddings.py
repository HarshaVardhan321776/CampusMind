import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "campusmind_docs"

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def load_document(file_path: str, file_type: str):
    """Load a PDF or DOCX file into LangChain Document objects."""
    if file_type == "pdf":
        loader = PyPDFLoader(file_path)
    elif file_type == "docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    return loader.load()


def chunk_documents(documents, chunk_size: int = 1000, chunk_overlap: int = 150):
    """Split loaded documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)


def embed_and_store(chunks, source_filename: str, document_id: int):
    """Generate embeddings for chunks and store them in ChromaDB."""
    for chunk in chunks:
        chunk.metadata["source"] = source_filename
        chunk.metadata["document_id"] = document_id

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=CHROMA_DIR,
    )
    vectorstore.add_documents(chunks)
    vectorstore.persist()

    return len(chunks)


def process_document(file_path: str, file_type: str, source_filename: str, document_id: int) -> int:
    """Full pipeline: load -> chunk -> embed -> store. Returns number of chunks created."""
    documents = load_document(file_path, file_type)
    chunks = chunk_documents(documents)
    num_chunks = embed_and_store(chunks, source_filename, document_id)
    return num_chunks