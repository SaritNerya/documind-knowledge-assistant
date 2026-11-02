from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, Source
from app.services.llm import answer_from_context
from app.services.retrieval import search_chunks

router = APIRouter(tags=["chat"])

MIN_SCORE = 0.3  # סף ראשוני, נכוונן אותו בשלב 5
NOT_FOUND_ANSWER = "לא מצאתי מידע על כך במסמכים."


@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        chunks = search_chunks(db, current_user.id, data.question)
        relevant = [c for c in chunks if c["score"] >= MIN_SCORE]

        if not relevant:
            return AskResponse(answer=NOT_FOUND_ANSWER)

        answer = answer_from_context(data.question, relevant)
    except OpenAIError:
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # מקורות ייחודיים (מסמך + עמוד), עם הציון הגבוה ביותר לכל אחד
    unique = {}
    for c in relevant:
        key = (c["filename"], c["page"])
        if key not in unique or c["score"] > unique[key]["score"]:
            unique[key] = c
    sources = [
        Source(filename=c["filename"], page=c["page"], score=round(c["score"], 3))
        for c in unique.values()
    ]

    return AskResponse(answer=answer, sources=sources)