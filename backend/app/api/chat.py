import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Response
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, MessageOut, Source
from app.services.rag import answer_question

from datetime import datetime, timedelta, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

HISTORY_LIMIT = 6  # כמה הודעות אחרונות מועברות למודל


@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = time.perf_counter()

#limit daily questions
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    asked_today = (
        db.query(Message)
        .filter(Message.user_id == current_user.id, Message.role == "user", Message.created_at >= since)
        .count()
    )
    if asked_today >= settings.daily_question_limit:
        raise HTTPException(status_code=429, detail="הגעת למכסת השאלות היומית. נסי שוב מחר.")

    recent = (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )[::-1]
    history = [{"role": m.role, "content": m.content} for m in recent]

    try:
        result = answer_question(db, current_user.id, data.question, history)
    except OpenAIError:
        logger.exception("LLM call failed for user=%s", current_user.id)
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # שומרים רק אחרי שהכול הצליח, כדי שלא יישארו שאלות בלי תשובה
    db.add(Message(user_id=current_user.id, role="user", content=data.question))
    db.add(
        Message(
            user_id=current_user.id,
            role="assistant",
            content=result.answer,
            sources=result.sources,
        )
    )
    db.commit()

    logger.info(
        "ask user=%s found=%s web=%s latency=%.2fs",
        current_user.id, result.found, result.used_web, time.perf_counter() - start,
    )
    return AskResponse(answer=result.answer, sources=[Source(**s) for s in result.sources])


@router.get("/messages", response_model=list[MessageOut])
def get_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.id)
        .all()
    )


@router.delete("/messages", status_code=204)
def clear_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Message).filter(Message.user_id == current_user.id).delete()
    db.commit()
    return Response(status_code=204)