from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, owned_conversation
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, MessageOut, Source
from app.schemas.conversation import ConversationOut, ConversationRename
from app.services import conversations as service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_conversations(db, current_user.id)


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_conversation(db, current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    return service.get_messages(db, conversation)


@router.patch("/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    data: ConversationRename,
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    return service.rename_conversation(db, conversation, data.title)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    if_empty: bool = False,  # ?if_empty=true: מחיקה רק אם אין בשיחה הודעות ומסמכים
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    service.delete_conversation(db, conversation, only_if_empty=if_empty)
    return Response(status_code=204)


@router.post("/{conversation_id}/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    conversation: Conversation = Depends(owned_conversation),
    db: Session = Depends(get_db),
):
    result = service.ask_in_conversation(db, conversation, data.question)
    return AskResponse(answer=result.answer, sources=[Source(**s) for s in result.sources])
