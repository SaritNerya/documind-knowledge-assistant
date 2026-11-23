from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, owned_conversation
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import documents as service

router = APIRouter(tags=["documents"])


@router.get("/conversations/{conversation_id}/documents", response_model=list[DocumentOut])
def list_documents(
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    return service.list_documents(db, conversation)


@router.post(
    "/conversations/{conversation_id}/documents", response_model=DocumentOut, status_code=201
)
def upload_document(
    file: UploadFile = File(...),
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    return service.upload_document(db, conversation, file)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_document(db, document_id, current_user.id)
    return Response(status_code=204)
