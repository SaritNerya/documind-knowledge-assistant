from pathlib import Path

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.chunking import split_text
from app.services.embeddings import embed_texts
from app.services.extraction import extract_pages


def ingest_document(db: Session, document_id: int, path: Path) -> int:
    """מחלצת, מחלקת, יוצרת Embeddings ומוסיפה Chunks למסד. מחזירה את מספר הקטעים.
    לא מבצעת commit, זו אחריות הקורא."""
    pieces = []  # רשימה של (מספר עמוד, טקסט הקטע)
    for page in extract_pages(path):
        for text in split_text(page["text"]):
            pieces.append((page["page"], text))

    if not pieces:
        return 0

    if len(pieces) > 300:
        raise ValueError("Document too large")

    vectors = embed_texts([text for _, text in pieces])

    for index, ((page_num, text), vector) in enumerate(zip(pieces, vectors)):
        db.add(
            Chunk(
                document_id=document_id,
                page=page_num,
                chunk_index=index,
                content=text,
                embedding=vector,
            )
        )
    return len(pieces)