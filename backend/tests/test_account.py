"""פרופיל, נתוני שימוש, החלפת סיסמה ומחיקת חשבון (/auth/me)."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tests.conftest import requires_db

pytestmark = requires_db

PASSWORD = "password123"


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def signup(client, email, password=PASSWORD):
    client.post("/auth/register", json={"email": email, "password": password})
    return login(client, email, password)


def login(client, email, password=PASSWORD):
    res = client.post("/auth/login", data={"username": email, "password": password})
    if res.status_code != 200:
        return None
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_me_includes_profile_fields(client):
    headers = signup(client, "a@test.dev")
    me = client.get("/auth/me", headers=headers).json()
    assert me["email"] == "a@test.dev"
    assert me["display_name"] is None
    assert me["created_at"]


@pytest.mark.parametrize("sent, saved", [("  שרית  ", "שרית"), ("", None), ("   ", None)])
def test_update_display_name(client, sent, saved):
    headers = signup(client, "a@test.dev")
    res = client.patch("/auth/me", headers=headers, json={"display_name": sent})
    assert res.status_code == 200
    assert res.json()["display_name"] == saved


def test_display_name_too_long_is_422(client):
    headers = signup(client, "a@test.dev")
    res = client.patch("/auth/me", headers=headers, json={"display_name": "א" * 51})
    assert res.status_code == 422


def test_usage_counts_only_my_data(client, db):
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.question_usage import QuestionUsage

    signup(client, "a@test.dev")
    headers = login(client, "a@test.dev")
    signup(client, "b@test.dev")  # משתמשת נוספת עם נתונים משלה

    db.add_all([Conversation(id=1, user_id=1, title="א"), Conversation(id=2, user_id=1, title="ב"),
                Conversation(id=3, user_id=2, title="ג")])
    db.flush()
    db.add_all([Document(filename="a.pdf", stored_filename="a", user_id=1, conversation_id=1),
                Document(filename="b.pdf", stored_filename="b", user_id=2, conversation_id=3)])
    old = datetime.now() - timedelta(days=2)
    db.add_all([QuestionUsage(user_id=1), QuestionUsage(user_id=1, created_at=old),
                QuestionUsage(user_id=2)])
    db.commit()

    usage = client.get("/auth/me/usage", headers=headers).json()
    assert usage == {
        "documents": 1,
        "conversations": 2,
        "questions": 2,      # כולל שאלה ישנה
        "daily_limit": 30,
        "used_today": 1,     # רק ב-24 השעות האחרונות
    }


def test_change_password(client):
    headers = signup(client, "a@test.dev")

    wrong = client.post("/auth/me/password", headers=headers,
                        json={"current_password": "nope-nope", "new_password": "brand-new-pass"})
    assert wrong.status_code == 400

    short = client.post("/auth/me/password", headers=headers,
                        json={"current_password": PASSWORD, "new_password": "short"})
    assert short.status_code == 422

    ok = client.post("/auth/me/password", headers=headers,
                     json={"current_password": PASSWORD, "new_password": "brand-new-pass"})
    assert ok.status_code == 204
    assert login(client, "a@test.dev", PASSWORD) is None
    assert login(client, "a@test.dev", "brand-new-pass") is not None


def test_delete_account_requires_matching_email(client):
    headers = signup(client, "a@test.dev")
    res = client.request("DELETE", "/auth/me", headers=headers, json={"confirm_email": "b@test.dev"})
    assert res.status_code == 400
    assert client.get("/auth/me", headers=headers).status_code == 200  # לא נמחק


def test_delete_account_removes_everything_mine_only(client, db):
    from app.core.config import settings
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.user import User

    headers = signup(client, "a@test.dev")
    other = signup(client, "b@test.dev")
    mine = client.post("/conversations", headers=headers).json()["id"]
    theirs = client.post("/conversations", headers=other).json()["id"]
    stored = Path(settings.upload_dir) / "mine.pdf"
    stored.write_bytes(b"x")
    db.add(Document(filename="a.pdf", stored_filename=stored.name, user_id=1, conversation_id=mine))
    db.commit()

    res = client.request("DELETE", "/auth/me", headers=headers, json={"confirm_email": " A@Test.dev "})
    assert res.status_code == 204

    db.expire_all()
    assert db.query(User).filter(User.email == "a@test.dev").first() is None
    assert db.query(Document).count() == 0
    assert not stored.exists()
    assert [c.id for c in db.query(Conversation)] == [theirs]  # של המשתמשת השנייה נשארה
    assert client.get("/auth/me", headers=headers).status_code == 401  # הטוקן כבר לא תקף
