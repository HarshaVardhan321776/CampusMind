import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentOut
from app.services.embeddings import process_document

from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = settings.UPLOAD_DIR
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents uploaded by the current user."""
    return db.query(Document).filter(
        Document.uploaded_by == current_user.id
    ).order_by(Document.uploaded_at.desc()).all()


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload, extract, chunk, and embed a PDF or DOCX file."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    file_type = ext.replace(".", "")

    doc = Document(
        filename=file.filename,
        file_type=file_type,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        num_chunks = process_document(
            file_path=file_path,
            file_type=file_type,
            source_filename=file.filename,
            document_id=doc.id,
        )
        print(f"[CampusMind] Document #{doc.id} ({file.filename}) processed into {num_chunks} chunks.")
    except Exception as e:
        print(f"[CampusMind Error] Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    return doc


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document record."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.uploaded_by == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": "Document deleted successfully"}