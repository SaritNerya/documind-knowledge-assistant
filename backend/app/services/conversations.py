import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException
from openai import OpenAIError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.question_usage import QuestionUsage
from app.services.rag import RagResult, answer_question
from app.services.titles import DEFAULT_TITLE, smart_title, temporary_title

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 6  # כמה הודעות אחרונות מהשיחה מועברות למודל


def get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    """המקום היחיד שבודק בעלות על שיחה. שיחה של משתמש אחר נראית כאילו אינה קיימת (404)."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def list_conversations(db: Session, user_id: int) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )


def create_conversation(db: Session, user_id: int) -> Conversation:
    count = db.query(Conversation).filter(Conversation.user_id == user_id).count()
    if count >= settings.max_conversations_per_user:
        raise HTTPException(
            status_code=400,
            detail="הגעת למספר השיחות המקסימלי. מחקי שיחה ישנה כדי לפתוח שיחה חדשה.",
        )
    conversation = Conversation(user_id=user_id, title=DEFAULT_TITLE)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def rename_conversation(db: Session, conversation: Conversation, title: str) -> Conversation:
    # שינוי שם לא מעדכן את updated_at, כדי שהשיחה לא תקפוץ לראש הרשימה
    conversation.title = title
    conversation.auto_title = False  # שם שהמשתמש בחר לא יוחלף אוטומטית
    db.commit()
    db.refresh(conversation)
    return conversation


def is_empty(db: Session, conversation: Conversation) -> bool:
    """שיחה ריקה: אין בה אף הודעה ואף מסמך."""
    def has(model) -> bool:
        return db.query(model.id).filter(model.conversation_id == conversation.id).first() is not None

    return not has(Message) and not has(Document)


def delete_conversation(db: Session, conversation: Conversation, only_if_empty: bool = False) -> None:
    """only_if_empty: מוחק רק שיחה ריקה (לניקוי שיחה חדשה שעזבו בלי לכתוב בה). אחרת לא עושה כלום."""
    if only_if_empty and not is_empty(db, conversation):
        return
    # ההודעות, המסמכים והקטעים נמחקים במסד הנתונים דרך ON DELETE CASCADE.
    # את הקבצים עצמם מוחקים מהדיסק רק אחרי שהמחיקה במסד הצליחה.
    stored = [
        name for (name,) in
        db.query(Document.stored_filename).filter(Document.conversation_id == conversation.id)
    ]
    db.delete(conversation)
    db.commit()
    for name in stored:
        (Path(settings.upload_dir) / name).unlink(missing_ok=True)


def get_messages(db: Session, conversation: Conversation) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id)
        .all()
    )


def _questions_asked_today(db: Session, user_id: int) -> int:
    """מכסה יומית למשתמש, על פני כל השיחות שלו, גם כאלה שנמחקו."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return (
        db.query(QuestionUsage)
        .filter(QuestionUsage.user_id == user_id, QuestionUsage.created_at >= since)
        .count()
    )


def _owned_document_ids(
    db: Session, conversation: Conversation, document_ids: list[int] | None
) -> list[int] | None:
    """מוודא שכל המסמכים שנבחרו שייכים לשיחה. מסמך זר נראה כאילו אינו קיים (404)."""
    if document_ids is None:
        return None
    wanted = set(document_ids)
    found = {
        doc_id for (doc_id,) in
        db.query(Document.id).filter(Document.conversation_id == conversation.id, Document.id.in_(wanted))
    }
    if found != wanted:
        raise HTTPException(status_code=404, detail="Document not found")
    return sorted(found)


def ask_in_conversation(
    db: Session,
    conversation: Conversation,
    question: str,
    document_ids: list[int] | None = None,
) -> RagResult:
    start = time.perf_counter()
    user_id = conversation.user_id

    if _questions_asked_today(db, user_id) >= settings.daily_question_limit:
        raise HTTPException(status_code=429, detail="הגעת למכסת השאלות היומית. נסי שוב מחר.")
    document_ids = _owned_document_ids(db, conversation, document_ids)

    recent = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )[::-1]
    history = [{"role": m.role, "content": m.content} for m in recent]

    try:
        result = answer_question(db, conversation.id, question, history, document_ids=document_ids)
    except OpenAIError:
        logger.exception("LLM call failed for user=%s", user_id)
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # שומרים רק אחרי שהכול הצליח, כדי שלא יישארו שאלות בלי תשובה.
    # השאלה הראשונה נותנת כותרת זמנית, גם אם קודם נקבע שם זמני משם הקובץ.
    is_first_question = not recent
    if is_first_question and conversation.auto_title:
        conversation.title = temporary_title(question)
    conversation.updated_at = func.now()
    db.add_all([
        QuestionUsage(user_id=user_id),
        Message(conversation_id=conversation.id, role="user", content=question),
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
            sources=result.sources,
        ),
    ])
    db.commit()

    # רק אחרי שהתשובה נשמרה: כותרת חכמה. כישלון כאן לא משפיע על התשובה.
    if is_first_question and conversation.auto_title:
        _apply_smart_title(db, conversation, question, result.answer)

    logger.info(
        "ask user=%s conversation=%s found=%s web=%s latency=%.2fs",
        user_id, conversation.id, result.found, result.used_web, time.perf_counter() - start,
    )
    return result


def _apply_smart_title(db: Session, conversation: Conversation, question: str, answer: str) -> None:
    """מחליף את הכותרת הזמנית בכותרת מהמודל.
    העדכון מותנה ב-auto_title בתוך אותה שאילתה: אם המשתמשת שינתה את השם בזמן
    שהמודל עבד, השם שלה נשאר ולא נדרס."""
    title = smart_title(question, answer)
    if title is None:
        return  # הכותרת הזמנית נשארת; smart_title כבר רשם ב-log
    db.query(Conversation).filter(
        Conversation.id == conversation.id, Conversation.auto_title.is_(True)
    ).update({Conversation.title: title}, synchronize_session=False)
    db.commit()
    db.refresh(conversation)
