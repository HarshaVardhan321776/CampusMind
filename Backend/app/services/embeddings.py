import os
import numpy as np
import hashlib
import math

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.core.config import settings

CHROMA_DIR = settings.CHROMA_DIR
COLLECTION_NAME = "campusmind_docs"
# Chroma uses its lightweight built-in embedding model.
# We intentionally avoid SentenceTransformer/PyTorch because Render's
# free 512 MB instance cannot reliably run that stack.

class LightweightEmbeddings:
    def __init__(self, dimensions=256):
        self.dimensions = dimensions

    def _embed(self, text: str):
        vector = [0.0] * self.dimensions

        for word in text.lower().split():
            digest = hashlib.md5(word.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(
            sum(value * value for value in vector)
        )

        if magnitude > 0:
            vector = [
                value / magnitude
                for value in vector
            ]

        return vector

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)


_embedding_function = None


def get_embedding_function():
    global _embedding_function

    if _embedding_function is None:
        print("[CampusMind] Loading lightweight embedding function...")
        _embedding_function = LightweightEmbeddings(
            dimensions=256
        )

    return _embedding_function

# Initialize OCR Engine for scanned/handwritten documents
_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
        except Exception as e:
            print(f"[OCR Init Warning]: Could not initialize RapidOCR: {e}")
            _ocr_engine = False
    return _ocr_engine


def extract_pdf_with_ocr(file_path: str) -> list[Document]:
    """Extract text from scanned or image-based PDF using RapidOCR."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("[PDF Warning]: pypdfium2 not installed.")
        return []

    engine = get_ocr_engine()
    if not engine:
        return []

    documents = []
    try:
        pdf = pdfium.PdfDocument(file_path)
        for idx in range(len(pdf)):
            page = pdf[idx]

            # Render page to bitmap image
            bitmap = page.render(scale=1.5)
            pil_image = bitmap.to_pil()
            img_np = np.array(pil_image)

            ocr_res, _ = engine(img_np)
            if ocr_res:
                page_lines = [line[1] for line in ocr_res if line[1].strip()]
                page_text = "\n".join(page_lines)

                if len(page_text.strip()) > 10:
                    documents.append(
                        Document(
                            page_content=page_text.strip(),
                            metadata={
                                "source": file_path,
                                "page": idx + 1
                            }
                        )
                    )
    except Exception as e:
        print(f"[OCR Extraction Error] on {file_path}: {e}")

    return documents


def load_document(file_path: str, file_type: str) -> list[Document]:
    """Load a PDF or DOCX file with automatic fallback to OCR for scanned documents."""

    if file_type == "docx":
        # 1. Try Docx2txtLoader
        try:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()

            if docs and sum(len(d.page_content.strip()) for d in docs) > 0:
                return docs

        except Exception as e:
            print(f"[Docx2txtLoader Warning] on {file_path}: {e}")

        # 2. Native python-docx fallback
        try:
            import docx

            doc = docx.Document(file_path)
            full_text = []

            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())

            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(
                        cell.text.strip()
                        for cell in row.cells
                        if cell.text.strip()
                    )

                    if row_text:
                        full_text.append(row_text)

            text = "\n\n".join(full_text)

            if text.strip():
                return [
                    Document(
                        page_content=text.strip(),
                        metadata={"source": file_path}
                    )
                ]

        except Exception as e:
            print(f"[python-docx Error] on {file_path}: {e}")
            raise RuntimeError(
                f"Could not extract text from docx file: {e}"
            )

        return []

    elif file_type == "pdf":
        # 1. Attempt digital text extraction with PyPDFLoader
        digital_docs = []

        try:
            loader = PyPDFLoader(file_path)
            digital_docs = loader.load()
        except Exception as e:
            print(f"[PyPDFLoader Warning] on {file_path}: {e}")

        # Check quality of extracted digital text
        total_text_length = sum(
            len(doc.page_content.strip())
            for doc in digital_docs
        )

        num_pages = len(digital_docs) if digital_docs else 1
        avg_chars_per_page = total_text_length / max(1, num_pages)

        # If digital text is missing, very sparse, or empty, trigger OCR
        if total_text_length < 100 or avg_chars_per_page < 40:
            print(
                f"[CampusMind] Scanned/Image PDF detected for "
                f"'{os.path.basename(file_path)}' "
                f"(only {total_text_length} digital chars found). "
                f"Running OCR pipeline..."
            )

            ocr_docs = extract_pdf_with_ocr(file_path)

            if (
                ocr_docs
                and sum(len(d.page_content) for d in ocr_docs)
                > total_text_length
            ):
                print(
                    f"[CampusMind] OCR successfully extracted "
                    f"{len(ocr_docs)} pages with "
                    f"{sum(len(d.page_content) for d in ocr_docs)} characters!"
                )
                return ocr_docs

        return digital_docs

    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120
):
    """Split loaded documents into smaller overlapping chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return splitter.split_documents(documents)


def embed_and_store(
    chunks: list[Document],
    source_filename: str,
    document_id: int
):
    """Generate embeddings for chunks and store them in ChromaDB."""

    if not chunks:
        print(
            f"[Embed Warning]: No text chunks to embed "
            f"for {source_filename}"
        )
        return 0

    for chunk in chunks:
        chunk.metadata["source"] = source_filename
        chunk.metadata["document_id"] = document_id

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=CHROMA_DIR,
    )

    vectorstore.add_documents(chunks)
    vectorstore.persist()

    return len(chunks)


def process_document(
    file_path: str,
    file_type: str,
    source_filename: str,
    document_id: int
) -> int:
    """Full pipeline: load -> chunk -> embed -> store."""

    documents = load_document(file_path, file_type)
    chunks = chunk_documents(documents)
    num_chunks = embed_and_store(
        chunks,
        source_filename,
        document_id
    )

    return num_chunks
