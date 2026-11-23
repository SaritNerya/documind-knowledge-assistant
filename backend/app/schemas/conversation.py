from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.core.config import settings


class ConversationRename(BaseModel):
    title: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=settings.conversation_title_max_length,
        ),
    ]


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
