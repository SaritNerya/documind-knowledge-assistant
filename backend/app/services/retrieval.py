from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import embed_texts


def search_chunks(
    db: Session,
    user_id: int,
    queries: list[str] | str,
    top_k: int = 5,
    max_results: int = 8,
) -> list[dict]:
    """חיפוש סמנטי במסמכים של המשתמש בלבד, עם כמה שאילתות במקביל.
    מאחדת תוצאות, משאירה לכל קטע את הציון הטוב ביותר, ומסירה קטעים זהים."""
    if isinstance(queries, str):
        queries = [queries]

    vectors = embed_texts(queries)  # קריאה אחת ל-API לכל השאילתות
    best: dict[str, dict] = {}

    for vector in vectors:
        distance = Chunk.embedding.cosine_distance(vector)
        stmt = (
            select(Chunk.content, Chunk.page, Document.filename, distance.label("distance"))
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.user_id == user_id)
            .order_by(distance)
            .limit(top_k * 3)  # שולפים יותר, כי אחר כך מסירים כפילויות
        )
        for row in db.execute(stmt).all():
            key = " ".join(row.content.split())  # זיהוי קטעים זהים
            score = 1 - row.distance
            if key not in best or score > best[key]["score"]:
                best[key] = {
                    "content": row.content,
                    "page": row.page,
                    "filename": row.filename,
                    "score": score,
                }

    ranked = sorted(best.values(), key=lambda c: c["score"], reverse=True)
    return ranked[:max_results]


def get_document_overviews(
    db: Session, user_id: int, max_docs: int = 20, max_chars: int = 500
) -> list[dict]:
    """תחילת כל מסמך של המשתמש. מאפשרת לענות על שאלות על המסמכים עצמם
    (שם, נושא, קשר בין מסמכים)."""
    stmt = (
        select(Document.filename, Chunk.content)
        .join(Chunk, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id, Chunk.chunk_index == 0)
        .order_by(Document.filename)
    )
    overviews, seen = [], set()
    for filename, content in db.execute(stmt).all():
        if filename in seen:
            continue
        seen.add(filename)
        overviews.append({"filename": filename, "preview": content[:max_chars]})
    return overviews[:max_docs]