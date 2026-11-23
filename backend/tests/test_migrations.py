"""ההגירה ממבנה הנתונים הישן (הודעות ומסמכים לפי משתמש) לא מאבדת נתונים."""
from sqlalchemy import inspect, text

from tests.conftest import requires_db, reset_schema

pytestmark = requires_db

LEGACY = "שיחה קודמת"


def test_upgrade_keeps_every_message_and_document():
    from alembic import command
    from alembic.config import Config

    from app.core.database import engine

    reset_schema("0001")  # המבנה שיצר create_all לפני Alembic
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO users (id, email, hashed_password) VALUES "
            "(1, 'a@t.dev', 'x'), (2, 'b@t.dev', 'x'), (3, 'c@t.dev', 'x'), (4, 'd@t.dev', 'x')"
        ))
        conn.execute(text(
            "INSERT INTO messages (user_id, role, content) VALUES "
            "(1, 'user', 'a1'), (1, 'assistant', 'a2'), (1, 'user', 'a3'), "
            "(2, 'user', 'b1'), (2, 'assistant', 'b2')"
        ))
        # למשתמש 3 יש מסמך בלי הודעות; למשתמש 4 אין כלום
        conn.execute(text(
            "INSERT INTO documents (filename, stored_filename, user_id) VALUES "
            "('a.pdf', 'a', 1), ('c.pdf', 'c', 3)"
        ))

    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.upgrade(config, "head")  # הרצה חוזרת לא משנה דבר

    with engine.connect() as conn:
        messages = conn.execute(text(
            "SELECT m.content, c.user_id, c.title FROM messages m "
            "JOIN conversations c ON c.id = m.conversation_id ORDER BY m.id"
        )).all()
        assert [(m.content, m.user_id) for m in messages] == [
            ("a1", 1), ("a2", 1), ("a3", 1), ("b1", 2), ("b2", 2),
        ]
        assert {m.title for m in messages} == {LEGACY}

        conversations = conn.execute(text(
            "SELECT user_id, title FROM conversations ORDER BY user_id"
        )).all()
        assert [tuple(c) for c in conversations] == [(1, LEGACY), (2, LEGACY), (3, LEGACY)]

        documents = conn.execute(text(
            "SELECT d.filename, c.user_id, c.title FROM documents d "
            "JOIN conversations c ON c.id = d.conversation_id ORDER BY d.id"
        )).all()
        assert [tuple(d) for d in documents] == [("a.pdf", 1, LEGACY), ("c.pdf", 3, LEGACY)]

        usage = conn.execute(text("SELECT user_id FROM question_usage ORDER BY user_id")).scalars().all()
        assert usage == [1, 1, 2]  # רק שאלות של המשתמש, לא תשובות

    assert "user_id" not in {c["name"] for c in inspect(engine).get_columns("messages")}

    # חזרה אחורה ושוב קדימה לא מאבדת הודעות
    command.downgrade(config, "0001")
    command.upgrade(config, "head")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM messages")).scalar() == 5
