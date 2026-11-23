from pathlib import Path

import pytest
from openai import OpenAIError

from tests.conftest import requires_db

pytestmark = requires_db


@pytest.fixture
def client(db, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import conversations, titles
    from app.services.rag import RagResult

    calls = []

    def fake_answer(db, conversation_id, question, history, allow_web=True, document_ids=None):
        calls.append({
            "conversation_id": conversation_id,
            "question": question,
            "history": history,
            "document_ids": document_ids,
        })
        return RagResult(answer=f"תשובה ל: {question}", sources=[], found=True, used_web=False)

    monkeypatch.setattr(conversations, "answer_question", fake_answer)
    c = TestClient(app)
    c.rag_calls = calls

    # מודל הכותרות: מחזיר את מה ש-c.title_reply() מחזיר (או זורק). ברירת מחדל: תשובה ריקה,
    # כלומר כישלון, כך שבדיקות שלא עוסקות בכותרת חכמה רואות את הכותרת הזמנית.
    c.title_calls = []
    c.title_reply = lambda: ""

    def fake_title(question, answer_excerpt):
        c.title_calls.append({"question": question, "answer_excerpt": answer_excerpt})
        return c.title_reply()

    monkeypatch.setattr(titles, "generate_title", fake_title)
    return c


def login(client, email):
    client.post("/auth/register", json={"email": email, "password": "password123"})
    token = client.post("/auth/login", data={"username": email, "password": "password123"}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


@pytest.fixture
def alice(client):
    return login(client, "alice@test.dev")


@pytest.fixture
def bob(client):
    return login(client, "bob@test.dev")


def new_conversation(client, headers):
    res = client.post("/conversations", headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def ask(client, headers, cid, question="שאלה"):
    return client.post(f"/conversations/{cid}/ask", headers=headers, json={"question": question})


@pytest.mark.parametrize("method, path, body", [
    ("get", "/conversations/{id}/messages", None),
    ("patch", "/conversations/{id}", {"title": "x"}),
    ("delete", "/conversations/{id}", None),
    ("post", "/conversations/{id}/ask", {"question": "hi"}),
    ("get", "/conversations/{id}/documents", None),
])
def test_other_users_conversation_is_404(client, alice, bob, method, path, body):
    cid = new_conversation(client, alice)
    kwargs = {"json": body} if body else {}
    res = getattr(client, method)(path.format(id=cid), headers=bob, **kwargs)
    assert res.status_code == 404
    # ולא נגרם שום שינוי לשיחה של alice
    assert [c["id"] for c in client.get("/conversations", headers=alice).json()] == [cid]
    assert client.rag_calls == []


def test_other_users_conversation_upload_is_404(client, alice, bob):
    cid = new_conversation(client, alice)
    res = client.post(f"/conversations/{cid}/documents", headers=bob,
                      files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 404


def test_list_is_per_user(client, alice, bob):
    new_conversation(client, alice)
    assert client.get("/conversations", headers=bob).json() == []


def test_delete_removes_messages_documents_and_files(client, db, alice):
    from app.core.config import settings
    from app.models.document import Document
    from app.models.message import Message

    cid = new_conversation(client, alice)
    ask(client, alice, cid)
    stored = Path(settings.upload_dir) / "test-file.pdf"
    stored.write_bytes(b"x")
    db.add(Document(filename="a.pdf", stored_filename=stored.name, user_id=1, conversation_id=cid))
    db.commit()

    assert client.delete(f"/conversations/{cid}", headers=alice).status_code == 204
    assert db.query(Message).count() == 0
    assert db.query(Document).count() == 0
    assert not stored.exists()


def test_delete_if_empty_removes_only_empty_conversations(client, db, alice):
    from app.models.document import Document

    empty = new_conversation(client, alice)
    with_message = new_conversation(client, alice)
    with_document = new_conversation(client, alice)
    ask(client, alice, with_message)
    db.add(Document(filename="a.pdf", stored_filename="a.pdf", user_id=1, conversation_id=with_document))
    db.commit()

    for cid in (empty, with_message, with_document):
        res = client.delete(f"/conversations/{cid}?if_empty=true", headers=alice)
        assert res.status_code == 204

    remaining = {c["id"] for c in client.get("/conversations", headers=alice).json()}
    assert remaining == {with_message, with_document}


def test_delete_if_empty_on_other_users_conversation_is_404(client, alice, bob):
    cid = new_conversation(client, alice)
    assert client.delete(f"/conversations/{cid}?if_empty=true", headers=bob).status_code == 404
    assert len(client.get("/conversations", headers=alice).json()) == 1


def test_list_ordered_by_last_activity(client, alice):
    first = new_conversation(client, alice)
    second = new_conversation(client, alice)
    ids = lambda: [c["id"] for c in client.get("/conversations", headers=alice).json()]
    assert ids() == [second, first]

    ask(client, alice, first)
    assert ids() == [first, second]

    # שינוי שם לא מקפיץ שיחה לראש הרשימה
    client.patch(f"/conversations/{second}", headers=alice, json={"title": "חדש"})
    assert ids() == [first, second]


def test_default_title_from_first_question(client, alice):
    cid = new_conversation(client, alice)
    title = lambda: client.get("/conversations", headers=alice).json()[0]["title"]
    assert title() == "שיחה חדשה"

    ask(client, alice, cid, "  מה   " + "א" * 100)
    assert len(title()) == 50 and title().startswith("מה א") and title().endswith("…")

    ask(client, alice, cid, "שאלה שנייה")
    assert title().startswith("מה א")  # רק השאלה הראשונה קובעת


def test_manual_title_is_not_overwritten(client, alice):
    cid = new_conversation(client, alice)
    client.patch(f"/conversations/{cid}", headers=alice, json={"title": "  השם שלי  "})
    ask(client, alice, cid, "שאלה ראשונה")
    assert client.get("/conversations", headers=alice).json()[0]["title"] == "השם שלי"


@pytest.mark.parametrize("title", ["", "   ", "x" * 101])
def test_rename_validation(client, alice, title):
    cid = new_conversation(client, alice)
    res = client.patch(f"/conversations/{cid}", headers=alice, json={"title": title})
    assert res.status_code == 422


def test_conversation_limit(client, alice, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "max_conversations_per_user", 2)
    new_conversation(client, alice)
    new_conversation(client, alice)
    assert client.post("/conversations", headers=alice).status_code == 400


def test_history_comes_only_from_current_conversation(client, alice):
    a = new_conversation(client, alice)
    b = new_conversation(client, alice)
    ask(client, alice, a, "שאלה בשיחה א")
    for i in range(4):
        ask(client, alice, b, f"ב{i}")

    ask(client, alice, b, "אחרונה")
    last = client.rag_calls[-1]
    assert last["conversation_id"] == b
    assert len(last["history"]) == 6  # HISTORY_LIMIT
    assert all("שיחה א" not in m["content"] for m in last["history"])
    assert last["history"][0]["content"] == "ב1"  # 6 ההודעות האחרונות, לפי הסדר

    ask(client, alice, a, "המשך")
    assert [m["content"] for m in client.rag_calls[-1]["history"]] == [
        "שאלה בשיחה א", "תשובה ל: שאלה בשיחה א",
    ]


def add_documents(db, conversation_id, *names):
    from app.models.document import Document

    docs = [Document(filename=n, stored_filename=n, user_id=1, conversation_id=conversation_id)
            for n in names]
    db.add_all(docs)
    db.commit()
    return [d.id for d in docs]


def test_ask_searches_only_selected_documents(client, db, alice):
    cid = new_conversation(client, alice)
    first, second, _ = add_documents(db, cid, "a.pdf", "b.pdf", "c.pdf")

    res = client.post(f"/conversations/{cid}/ask", headers=alice,
                      json={"question": "שאלה", "document_ids": [second, first, second]})
    assert res.status_code == 200
    assert client.rag_calls[-1]["document_ids"] == [first, second]  # בלי כפילויות, ממוין

    ask(client, alice, cid)  # בלי document_ids: כל המסמכים בשיחה
    assert client.rag_calls[-1]["document_ids"] is None


def test_ask_with_document_from_another_conversation_is_404(client, db, alice):
    mine = new_conversation(client, alice)
    other = new_conversation(client, alice)
    (foreign,) = add_documents(db, other, "x.pdf")

    res = client.post(f"/conversations/{mine}/ask", headers=alice,
                      json={"question": "שאלה", "document_ids": [foreign]})
    assert res.status_code == 404
    assert client.rag_calls == []


def test_ask_with_empty_document_selection_is_422(client, alice):
    cid = new_conversation(client, alice)
    res = client.post(f"/conversations/{cid}/ask", headers=alice,
                      json={"question": "שאלה", "document_ids": []})
    assert res.status_code == 422


def test_messages_endpoint_returns_conversation_messages(client, alice):
    cid = new_conversation(client, alice)
    ask(client, alice, cid, "שלום")
    messages = client.get(f"/conversations/{cid}/messages", headers=alice).json()
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "שלום"), ("assistant", "תשובה ל: שלום"),
    ]


def test_daily_limit_is_per_user_and_survives_deletion(client, alice, bob, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "daily_question_limit", 2)
    a = new_conversation(client, alice)
    b = new_conversation(client, alice)
    assert ask(client, alice, a).status_code == 200
    assert ask(client, alice, b).status_code == 200

    client.delete(f"/conversations/{a}", headers=alice)  # מחיקה לא מאפסת את המכסה
    c = new_conversation(client, alice)
    assert ask(client, alice, c).status_code == 429
    # המכסה של משתמש אחר לא מושפעת
    assert ask(client, bob, new_conversation(client, bob)).status_code == 200


def test_llm_failure_saves_nothing(client, alice, monkeypatch):
    from app.services import conversations

    def broken(*args, **kwargs):
        raise OpenAIError("down")

    monkeypatch.setattr(conversations, "answer_question", broken)
    cid = new_conversation(client, alice)
    assert ask(client, alice, cid).status_code == 502
    assert client.get(f"/conversations/{cid}/messages", headers=alice).json() == []
    assert client.get("/conversations", headers=alice).json()[0]["title"] == "שיחה חדשה"


def test_upload_limit_checked_before_embeddings(client, db, alice, monkeypatch):
    from app.core.config import settings
    from app.models.document import Document
    from app.services import documents

    monkeypatch.setattr(settings, "max_docs_per_conversation", 1)
    monkeypatch.setattr(documents, "ingest_document", lambda *a: pytest.fail("ingest was called"))
    cid = new_conversation(client, alice)
    db.add(Document(filename="a.pdf", stored_filename="a.pdf", user_id=1, conversation_id=cid))
    db.commit()

    res = client.post(f"/conversations/{cid}/documents", headers=alice,
                      files={"file": ("b.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 400
    # בשיחה אחרת אפשר להעלות, והקובץ מקבל את שם השיחה הזמני
    monkeypatch.setattr(documents, "ingest_document", lambda *a: 1)
    other = new_conversation(client, alice)
    res = client.post(f"/conversations/{other}/documents", headers=alice,
                      files={"file": ("דוח.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 201
    listed = client.get(f"/conversations/{other}/documents", headers=alice).json()
    assert [d["filename"] for d in listed] == ["דוח.pdf"]
    assert client.get("/conversations", headers=alice).json()[0]["title"] == "דוח.pdf"


# ===== כותרת חכמה (המודל מוחלף ב-client.title_reply) =====

def titles_of(client, headers):
    return {c["id"]: c["title"] for c in client.get("/conversations", headers=headers).json()}


def test_smart_title_after_first_answer_only(client, alice):
    client.title_reply = lambda: "ימי חופשה לעובדים"
    cid = new_conversation(client, alice)

    res = ask(client, alice, cid, "כמה ימי חופשה מגיעים לי בשנה הראשונה?")
    assert res.json()["title"] == "ימי חופשה לעובדים"  # מוחזר בתשובה, בלי קריאה נוספת
    assert titles_of(client, alice)[cid] == "ימי חופשה לעובדים"
    assert client.title_calls[0]["answer_excerpt"].startswith("תשובה ל:")

    client.title_reply = lambda: "כותרת אחרת לגמרי"
    res = ask(client, alice, cid, "ומה לגבי מחלה?")
    assert res.json()["title"] == "ימי חופשה לעובדים"
    assert len(client.title_calls) == 1  # רק אחרי התשובה הראשונה


def raise_timeout():
    raise OpenAIError("timeout")


@pytest.mark.parametrize("reply", [
    raise_timeout,                              # שגיאה או timeout
    lambda: "",                                 # ריקה
    lambda: "חופשה",                            # מילה אחת: קצרה מדי
    lambda: "אחת שתיים שלוש ארבע חמש שש",       # 6 מילים: ארוכה מדי
])
def test_smart_title_failure_keeps_temporary_title(client, alice, reply):
    client.title_reply = reply
    cid = new_conversation(client, alice)

    res = ask(client, alice, cid, "כמה ימי חופשה?")
    assert res.status_code == 200
    assert res.json()["answer"] == "תשובה ל: כמה ימי חופשה?"  # התשובה לא נפגעה
    assert res.json()["title"] == "כמה ימי חופשה?"
    assert titles_of(client, alice)[cid] == "כמה ימי חופשה?"


def test_manual_title_is_never_replaced_by_smart_title(client, alice):
    client.title_reply = lambda: "כותרת מהמודל"
    cid = new_conversation(client, alice)
    client.patch(f"/conversations/{cid}", headers=alice, json={"title": "השם שלי"})

    res = ask(client, alice, cid)
    assert res.json()["title"] == "השם שלי"
    assert client.title_calls == []  # בכלל לא פונים למודל


def test_rename_while_model_works_is_not_overwritten(client, alice):
    from app.core.database import SessionLocal
    from app.models.conversation import Conversation

    cid = new_conversation(client, alice)

    def rename_meanwhile():
        # המשתמשת משנה שם בזמן שהמודל מייצר כותרת (עדכון ממסד נפרד, כמו בקשה מקבילה)
        with SessionLocal() as other:
            other.query(Conversation).filter(Conversation.id == cid).update(
                {Conversation.title: "שם ידני", Conversation.auto_title: False}
            )
            other.commit()
        return "כותרת מהמודל"

    client.title_reply = rename_meanwhile
    res = ask(client, alice, cid)
    assert res.json()["title"] == "שם ידני"
    assert titles_of(client, alice)[cid] == "שם ידני"


def test_smart_title_does_not_touch_other_users(client, alice, bob):
    client.title_reply = lambda: "ימי חופשה לעובדים"
    mine = new_conversation(client, alice)
    theirs = new_conversation(client, bob)
    before = titles_of(client, bob)

    ask(client, alice, mine)
    assert titles_of(client, bob) == before
    assert before[theirs] == "שיחה חדשה"


def test_smart_title_is_not_counted_in_daily_limit(client, alice, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "daily_question_limit", 1)
    client.title_reply = lambda: "ימי חופשה לעובדים"
    assert ask(client, alice, new_conversation(client, alice)).status_code == 200
    assert len(client.title_calls) == 1
    # השאלה השנייה נחסמת בגלל השאלה הראשונה בלבד, לא בגלל קריאת הכותרת
    assert ask(client, alice, new_conversation(client, alice)).status_code == 429


@pytest.mark.parametrize("raw, expected", [
    ('"ימי חופשה לעובדים."', "ימי חופשה לעובדים"),
    ("  Vacation   policy  ", "Vacation policy"),
    ("“נהלי נסיעות”", "נהלי נסיעות"),
    ("", None),
    ("מילה", None),
    ("a b c d e f", None),
])
def test_clean_title(raw, expected):
    from app.services.titles import clean_title

    assert clean_title(raw) == expected
