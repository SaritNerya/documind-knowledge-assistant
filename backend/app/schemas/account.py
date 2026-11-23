from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

DISPLAY_NAME_MAX_LENGTH = 50


class ProfileUpdate(BaseModel):
    # מחרוזת ריקה מאפסת את השם (הפרונט יחזור להציג את תחילת האימייל)
    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=DISPLAY_NAME_MAX_LENGTH)
    ]


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class AccountDelete(BaseModel):
    confirm_email: str  # אישור כפול: המשתמשת מקלידה את האימייל שלה


class UsageOut(BaseModel):
    documents: int
    conversations: int
    questions: int          # כל השאלות אי פעם, כולל בשיחות שנמחקו
    daily_limit: int
    used_today: int         # ב-24 השעות האחרונות
