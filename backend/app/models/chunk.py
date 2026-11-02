from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.services.embeddings import EMBEDDING_DIM


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int]
    chunk_index: Mapped[int]
    content: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))