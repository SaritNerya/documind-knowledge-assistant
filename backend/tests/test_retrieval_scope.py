from tests.conftest import requires_db

pytestmark = requires_db

DIM = 1536


def test_search_only_in_conversation_documents(db, monkeypatch):
    from app.models.chunk import Chunk
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.user import User
    from app.services import retrieval

    vector = [1.0] + [0.0] * (DIM - 1)
    monkeypatch.setattr(retrieval, "embed_texts", lambda texts: [vector for _ in texts])

    # flush אחרי כל שלב: בלי relationship במודלים, SQLAlchemy לא יודע לסדר את ההכנסות לפי ה-FK
    db.add(User(id=1, email="u@test.dev", hashed_password="x"))
    db.flush()
    db.add_all([Conversation(id=1, user_id=1, title="א"), Conversation(id=2, user_id=1, title="ב")])
    db.flush()
    db.add_all([
        Document(id=1, filename="mine.pdf", stored_filename="1", user_id=1, conversation_id=1),
        Document(id=2, filename="other.pdf", stored_filename="2", user_id=1, conversation_id=2),
    ])
    db.flush()
    db.add_all([
        Chunk(document_id=1, page=1, chunk_index=0, content="בשיחה 1", embedding=vector),
        Chunk(document_id=2, page=1, chunk_index=0, content="בשיחה 2", embedding=vector),
    ])
    db.commit()

    found = retrieval.search_chunks(db, 1, "שאלה")
    assert [c["filename"] for c in found] == ["mine.pdf"]
    overviews = retrieval.get_document_overviews(db, 1)
    assert [o["filename"] for o in overviews] == ["mine.pdf"]
    assert retrieval.search_chunks(db, 3, "שאלה") == []  # שיחה בלי מסמכים
