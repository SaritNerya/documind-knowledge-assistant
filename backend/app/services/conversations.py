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

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 6  # כמה הודעות אחרונות מהשיחה מועברות למודל
DEFAULT_TITLE = "שיחה חדשה"


def make_title(question: str) -> str:
    """כותרת מהשאלה הראשונה: רווחים מצומצמים, חיתוך לאורך המוגדר עם '…'."""
    text = " ".join(question.split())
    limit = settings.auto_title_length
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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


def delete_conversation(db: Session, conversation: Conversation) -> None:
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


def ask_in_conversation(db: Session, conversation: Conversation, question: str) -> RagResult:
    start = time.perf_counter()
    user_id = conversation.user_id

    if _questions_asked_today(db, user_id) >= settings.daily_question_limit:
        raise HTTPException(status_code=429, detail="הגעת למכסת השאלות היומית. נסי שוב מחר.")

    recent = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )[::-1]
    history = [{"role": m.role, "content": m.content} for m in recent]

    try:
        result = answer_question(db, conversation.id, question, history)
    except OpenAIError:
        logger.exception("LLM call failed for user=%s", user_id)
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # שומרים רק אחרי שהכול הצליח, כדי שלא יישארו שאלות בלי תשובה
    # השאלה הראשונה קובעת את השם, גם אם קודם נקבע שם זמני משם הקובץ
    if not recent and conversation.auto_title:
        conversation.title = make_title(question)
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

    logger.info(
        "ask user=%s conversation=%s found=%s web=%s latency=%.2fs",
        user_id, conversation.id, result.found, result.used_web, time.perf_counter() - start,
    )
    return result
