from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

class Source(BaseModel):
    filename: str
    page: int
    score: float

class AskResponse(BaseModel):
    answer: str
    sources: list[Source] = []