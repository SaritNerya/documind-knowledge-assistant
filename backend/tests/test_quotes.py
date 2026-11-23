"""בחירת המשפט להדגשה, וצירוף הציטוט למקורות. בלי מסד נתונים ובלי OpenAI."""
from app.services.quotes import best_sentence

PASSAGE = (
    "עובד חדש מקבל מחשב נייד ותג כניסה. "
    "ימי החופשה הם 12 ימים בשנה הראשונה. "
    "ההחזר על נסיעות ניתן לפי תעריף התחבורה הציבורית."
)


def test_picks_the_sentence_closest_to_the_answer():
    answer = "לפי המסמך, בשנה הראשונה מגיעים לך 12 ימי חופשה."
    assert best_sentence(PASSAGE, answer) == "ימי החופשה הם 12 ימים בשנה הראשונה."


def test_hebrew_prefixes_still_match():
    # "וההחזר" ו"נסיעות" בתשובה, "ההחזר" ו"נסיעות" בקטע
    assert best_sentence(PASSAGE, "וההחזר על הנסיעות").startswith("ההחזר על נסיעות")


def test_returned_sentence_is_an_exact_substring():
    sentence = best_sentence(PASSAGE, "מחשב נייד")
    assert sentence in PASSAGE  # הפרונט מחפש אותו בטקסט כדי לסמן


def test_no_shared_words_returns_none():
    assert best_sentence(PASSAGE, "xyz") is None


def test_rag_sources_include_quote_and_highlight(monkeypatch):
    from app.services import rag

    chunk = {"content": f"  {PASSAGE}  ", "page": 3, "filename": "נהלים.pdf", "score": 0.91}
    monkeypatch.setattr(rag, "rewrite_queries", lambda q, h: [q])
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [chunk])
    monkeypatch.setattr(rag, "get_document_overviews", lambda *a, **k: [])
    monkeypatch.setattr(rag, "generate_answer", lambda *a: {
        "found": True, "needs_web": False, "used": [1],
        "answer": "בשנה הראשונה מגיעים 12 ימי חופשה.",
    })

    result = rag.answer_question(None, 1, "כמה ימי חופשה?", [])
    (source,) = result.sources
    assert source["quote"] == PASSAGE  # בלי רווחים בקצוות
    assert source["highlight"] == "ימי החופשה הם 12 ימים בשנה הראשונה."
    assert source["highlight"] in source["quote"]
