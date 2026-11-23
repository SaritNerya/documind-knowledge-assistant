"""כותרות שיחה: כותרת זמנית מיידית, וכותרת "חכמה" מהמודל אחרי התשובה הראשונה.

הכותרת החכמה היא תוספת נוחות בלבד. כל כישלון (שגיאה, timeout, תשובה לא תקינה)
נרשם ב-log ומחזיר None, והשיחה נשארת עם הכותרת הזמנית.
"""
import logging

from openai import OpenAIError

from app.core.config import settings
from app.services.llm import generate_title

logger = logging.getLogger(__name__)

DEFAULT_TITLE = "שיחה חדשה"
ANSWER_EXCERPT_CHARS = 300  # כמה מתחילת התשובה נשלח למודל
MIN_WORDS, MAX_WORDS = 2, 5
STRIP_CHARS = " \t\n\"'“”„«»`.״׳"  # מרכאות ונקודות שהמודל מוסיף לפעמים למרות ההוראה


def temporary_title(text: str) -> str:
    """כותרת מיידית: רווחים מצומצמים, חיתוך לאורך המוגדר עם '…'."""
    text = " ".join(text.split())
    limit = settings.auto_title_length
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def clean_title(raw: str) -> str | None:
    """מנקה את תשובת המודל ומחזירה כותרת תקינה, או None אם היא ריקה, קצרה או ארוכה מדי."""
    title = " ".join(raw.split()).strip(STRIP_CHARS)
    words = len(title.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        return None
    if len(title) > settings.conversation_title_max_length:
        return None
    return title


def smart_title(question: str, answer: str) -> str | None:
    """כותרת של 2 עד 5 מילים מהמודל, או None בכל כישלון (לא זורקת)."""
    try:
        raw = generate_title(question, answer[:ANSWER_EXCERPT_CHARS])
    except OpenAIError:
        logger.warning("smart title: model call failed", exc_info=True)
        return None
    title = clean_title(raw)
    if title is None:
        logger.warning("smart title: rejected model output %r", raw[:100])
    return title
