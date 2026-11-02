from fastapi import APIRouter, Depends, HTTPException, Response
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, MessageOut, Source
from app.services.llm import answer_from_context
from app.services.retrieval import search_chunks

router = APIRouter(tags=["chat"])

MIN_SCORE = 0.3  # סף ראשוני, נכוונן אותו בשלב 5
NOT_FOUND_ANSWER = "לא מצאתי מידע על כך במסמכים."


def build_sources(relevant: list[dict]) -> list[Source]:
    """מקורות ייחודיים (מסמך + עמוד), עם הציון הגבוה ביותר לכל אחד."""
    unique = {}
    for c in relevant:
        key = (c["filename"], c["page"])
        if key not in unique or c["score"] > unique[key]["score"]:
            unique[key] = c
    return [
        Source(filename=c["filename"], page=c["page"], score=round(c["score"], 3))
        for c in unique.values()
    ]


@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        chunks = search_chunks(db, current_user.id, data.question)
        relevant = [c for c in chunks if c["score"] >= MIN_SCORE]

        if relevant:
            answer = answer_from_context(data.question, relevant)
            sources = build_sources(relevant)
        else:
            answer = NOT_FOUND_ANSWER
            sources = []
    except OpenAIError:
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # שומרים רק אחרי שהכול הצליח, כדי שלא יישארו שאלות בלי תשובה
    db.add(Message(user_id=current_user.id, role="user", content=data.question))
    db.add(
        Message(
            user_id=current_user.id,
            role="assistant",
            content=answer,
            sources=[s.model_dump() for s in sources],
        )
    )
    db.commit()

    return AskResponse(answer=answer, sources=sources)


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