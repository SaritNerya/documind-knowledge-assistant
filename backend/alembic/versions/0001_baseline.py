"""baseline: the schema that create_all built before Alembic

Existing databases (local and Azure) already have these tables, so every
step only creates what is missing. The same command works on an empty
database and on one that was created by Base.metadata.create_all.

Revision ID: 0001
Revises:
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 1536  # קבוע כאן בכוונה: הגירה מתעדת את המצב ברגע שנכתבה


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "documents" not in existing:
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("stored_filename", sa.String(), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_documents_user_id", "documents", ["user_id"])

    if "chunks" not in existing:
        op.create_table(
            "chunks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "document_id",
                sa.Integer(),
                sa.ForeignKey("documents.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("page", sa.Integer(), nullable=False),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        )
        op.create_index("ix_chunks_document_id", "chunks", ["document_id"])

    if "messages" not in existing:
        # המבנה הישן, עם user_id. הגירה 0002 מעבירה אותו לשיחות.
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("sources", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_messages_user_id", "messages", ["user_id"])


def downgrade() -> None:
    # בכוונה לא מוחקים כלום: אלה הטבלאות עם כל הנתונים של המשתמשים
    pass
