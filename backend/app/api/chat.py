from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse
from app.services.llm import ask_llm

router = APIRouter(tags=["chat"])

@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        answer = ask_llm(data.question)
    except OpenAIError:
        raise HTTPException(status_code=502, detail="LLM service unavailable")
    return AskResponse(answer=answer)