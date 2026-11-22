from datetime import datetime

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QuestionUsage(Base):
    """שורה לכל שאלה שנענתה. נפרדת מההודעות כדי שמחיקת שיחה לא תאפס את המכסה היומית."""

    __tablename__ = "question_usage"
    __table_args__ = (Index("ix_question_usage_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
