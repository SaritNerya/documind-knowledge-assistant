import shutil
import uuid
from pathlib import Path

from openai import OpenAIError
from app.services.ingestion import ingest_document

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    existing = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.filename == file.filename)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="A document with this name already exists")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        filename=file.filename,
        stored_filename=stored_name,
        user_id=current_user.id,
    )
    db.add(doc)
    db.flush()  # נותן ל-doc מזהה (id) בלי לשמור סופית
    
    try:
        chunk_count = ingest_document(db, doc.id, file_path)
    except OpenAIError:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail="Embedding service unavailable")
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not read the file")

    if chunk_count == 0:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No text found in the file")

    db.commit()
    db.refresh(doc)
    return doc

@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    (UPLOAD_DIR / doc.stored_filename).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    return Response(status_code=204)