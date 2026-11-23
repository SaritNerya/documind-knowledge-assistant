import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from openai import OpenAIError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.document import Document
from app.services.titles import DEFAULT_TITLE, temporary_title
from app.services.ingestion import ingest_document

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def list_documents(db: Session, conversation: Conversation) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.conversation_id == conversation.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


def _check_upload_allowed(db: Session, conversation: Conversation, file: UploadFile) -> str:
    """כל הבדיקות לפני שמשלמים על Embeddings. מחזירה את סיומת הקובץ."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    if file.size and file.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.max_upload_mb} MB)")

    in_conversation = db.query(Document).filter(Document.conversation_id == conversation.id)
    if in_conversation.count() >= settings.max_docs_per_conversation:
        raise HTTPException(status_code=400, detail="Document limit reached for this conversation")
    user_total = db.query(Document).filter(Document.user_id == conversation.user_id).count()
    if user_total >= settings.max_docs_per_user:
        raise HTTPException(status_code=400, detail="Document limit reached")
    if in_conversation.filter(Document.filename == file.filename).first():
        raise HTTPException(status_code=409, detail="A document with this name already exists")
    return ext


def upload_document(db: Session, conversation: Conversation, file: UploadFile) -> Document:
    ext = _check_upload_allowed(db, conversation, file)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        filename=file.filename,
        stored_filename=stored_name,
        user_id=conversation.user_id,
        conversation_id=conversation.id,
    )
    db.add(doc)
    db.flush()  # נותן ל-doc מזהה (id) בלי לשמור סופית

    try:
        chunk_count = ingest_document(db, doc.id, file_path)
        if chunk_count == 0:
            raise HTTPException(status_code=400, detail="No text found in the file")
    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        if isinstance(exc, OpenAIError):
            raise HTTPException(status_code=502, detail="Embedding service unavailable")
        raise HTTPException(status_code=400, detail="Could not read the file")

    # שם זמני לשיחה חדשה, עד שהשאלה הראשונה תקבע את השם
    if conversation.auto_title and conversation.title == DEFAULT_TITLE:
        conversation.title = temporary_title(file.filename)
    conversation.updated_at = func.now()
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: int, user_id: int) -> None:
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    (UPLOAD_DIR / doc.stored_filename).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
