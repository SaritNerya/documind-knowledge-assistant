from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    filename: str            # שם קובץ, או כותרת עמוד אינטרנט
    page: int = 0
    score: float = 0.0
    url: str | None = None   # רק למקורות מהאינטרנט


class AskResponse(BaseModel):
    answer: str
    sources: list[Source] = []


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: list[Source] | None = None
    model_config = {"from_attributes": True}