"""הגדרות משותפות לבדיקות.

בדיקות שצריכות מסד נתונים רצות רק מול TEST_DATABASE_URL, ששם המסד בו חייב להסתיים
ב-_test. כך אי אפשר להריץ אותן בטעות על המסד האמיתי. בלי המשתנה הן מדולגות.
"""
import os
import tempfile

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
HAS_TEST_DB = TEST_DATABASE_URL.rsplit("/", 1)[-1].split("?")[0].endswith("_test")

# חייב לקרות לפני שמשהו מייבא את app.core.config. משתני סביבה גוברים על .env.
os.environ["DATABASE_URL"] = (
    TEST_DATABASE_URL if HAS_TEST_DB else "postgresql+psycopg2://invalid:invalid@invalid/invalid_test"
)
os.environ["SECRET_KEY"] = "test-secret"
os.environ["OPENAI_API_KEY"] = "test-key"  # כל קריאה ל-OpenAI בבדיקות מוחלפת ב-mock
os.environ["INVITE_CODE"] = ""
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="documind-test-uploads-")

requires_db = pytest.mark.skipif(not HAS_TEST_DB, reason="TEST_DATABASE_URL (..._test) not set")


def reset_schema(revision: str = "head") -> None:
    """מוחק את כל הסכמה ומריץ את הגירות Alembic עד revision."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from app.core.database import engine

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    command.upgrade(Config("alembic.ini"), revision)


@pytest.fixture(scope="session")
def migrated_db():
    reset_schema()


@pytest.fixture
def db(migrated_db):
    """מסד נקי לכל בדיקה (הסכמה נשארת, הנתונים נמחקים)."""
    from sqlalchemy import text

    from app.core.database import SessionLocal, engine

    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE users, conversations, messages, documents, chunks, question_usage "
            "RESTART IDENTITY CASCADE"
        ))
    session = SessionLocal()
    yield session
    session.close()
