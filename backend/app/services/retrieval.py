from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import embed_text


def search_chunks(db: Session, user_id: int, question: str, top_k: int = 4) -> list[dict]:
    """מחזירה את top_k הקטעים הכי קרובים לשאלה, מתוך המסמכים של המשתמש בלבד."""
    question_vector = embed_text(question)
    distance = Chunk.embedding.cosine_distance(question_vector)

    stmt = (
        select(Chunk.content, Chunk.page, Document.filename, distance.label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id)  # important: filter by user_id to ensure only the user's documents are searched
        .order_by(distance)
        .limit(top_k)
    )

    return [
        {
            "content": row.content,
            "page": row.page,
            "filename": row.filename,
            "score": 1 - row.distance,  # דמיון: גבוה יותר = קרוב יותר
        }
        for row in db.execute(stmt).all()
    ]