"""פעולות על החשבון של המשתמשת המחוברת: פרופיל, נתוני שימוש, סיסמה ומחיקה."""
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.question_usage import QuestionUsage
from app.models.user import User
from app.services.conversations import questions_asked_today


def update_display_name(db: Session, user: User, display_name: str) -> User:
    user.display_name = display_name or None  # ריק: חזרה לברירת המחדל
    db.commit()
    db.refresh(user)
    return user


def usage(db: Session, user: User) -> dict:
    """סטטיסטיקה לפרופיל ומצב המכסה היומית, בקריאה אחת."""
    def count(model) -> int:
        return db.query(model).filter(model.user_id == user.id).count()

    return {
        "documents": count(Document),
        "conversations": count(Conversation),
        "questions": count(QuestionUsage),
        "daily_limit": settings.daily_question_limit,
        "used_today": questions_asked_today(db, user.id),
    }


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="הסיסמה הנוכחית שגויה")
    user.hashed_password = hash_password(new_password)
    db.commit()


def delete_account(db: Session, user: User, confirm_email: str) -> None:
    """מוחקת את החשבון וכל מה שבו, בטרנזקציה אחת.

    קודם השיחות: מחיקתן מוחקת במסד (CASCADE) את ההודעות, המסמכים והקטעים.
    זה חייב לקרות לפני מחיקת המשתמשת, כי documents.user_id הוגדר בלי CASCADE.
    הקבצים עצמם נמחקים מהדיסק רק אחרי שהמחיקה במסד הצליחה."""
    if confirm_email.strip().lower() != user.email.lower():
        raise HTTPException(status_code=400, detail="האימייל שהוקלד לא תואם לחשבון")
    stored = [name for (name,) in db.query(Document.stored_filename).filter(Document.user_id == user.id)]
    db.query(Conversation).filter(Conversation.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    for name in stored:
        (Path(settings.upload_dir) / name).unlink(missing_ok=True)
