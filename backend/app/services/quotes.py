"""בחירת המשפט להדגשה בתוך קטע מקור.

בלי קריאה למודל: מפרקים את הקטע למשפטים, ובוחרים את המשפט שיש לו הכי הרבה מילים
משותפות עם התשובה. מספיק טוב להראות למשתמש "מכאן זה נלקח", מהיר וחינמי.
"""
import re

SENTENCE_END = re.compile(r"(?<=[.!?;:\n])\s+")
WORD = re.compile(r"\w+")
# אותיות שימוש בעברית (ו, ה, ב, ל, מ, ש, כ): "והחופשה" ו"חופשה" נחשבות אותה מילה
HEBREW_PREFIXES = "והבלמשכ"
MIN_WORD_LENGTH = 2


def _normalize(word: str) -> str:
    word = word.lower()
    while len(word) > 3 and word[0] in HEBREW_PREFIXES:
        word = word[1:]
    return word


def _words(text: str) -> set[str]:
    return {_normalize(w) for w in WORD.findall(text) if len(w) >= MIN_WORD_LENGTH}


def best_sentence(passage: str, reference: str) -> str | None:
    """המשפט מתוך passage שהכי דומה ל-reference (התשובה). None אם אין אף מילה משותפת.
    המשפט מוחזר בדיוק כפי שהוא מופיע ב-passage, כדי שהפרונט יוכל למצוא ולסמן אותו."""
    reference_words = _words(reference)
    best, best_overlap = None, 0
    for sentence in SENTENCE_END.split(passage.strip()):
        overlap = len(_words(sentence) & reference_words)
        if overlap > best_overlap:
            best, best_overlap = sentence.strip(), overlap
    return best
