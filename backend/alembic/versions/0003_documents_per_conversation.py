"""documents belong to a conversation; conversations remember if the title is automatic

1. conversations.auto_title (default true; a manual rename sets it to false).
2. documents.conversation_id: each user's existing documents move to their
   "שיחה קודמת" conversation from 0002, created now if the user had
   documents but no messages.

Safe to run again: each step checks the current schema first.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

LEGACY_TITLE = "שיחה קודמת"


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()

    if "auto_title" not in _columns("conversations"):
        op.add_column(
            "conversations",
            sa.Column("auto_title", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    if "conversation_id" in _columns("documents"):
        return  # המסמכים כבר משויכים לשיחות

    op.add_column("documents", sa.Column("conversation_id", sa.Integer(), nullable=True))

    owners = bind.execute(sa.text("SELECT DISTINCT user_id FROM documents")).scalars().all()
    for user_id in owners:
        conversation_id = bind.execute(
            sa.text(
                "SELECT id FROM conversations WHERE user_id = :user_id AND title = :title "
                "ORDER BY id LIMIT 1"
            ),
            {"user_id": user_id, "title": LEGACY_TITLE},
        ).scalar()
        if conversation_id is None:
            conversation_id = bind.execute(
                sa.text(
                    "INSERT INTO conversations (user_id, title) VALUES (:user_id, :title) "
                    "RETURNING id"
                ),
                {"user_id": user_id, "title": LEGACY_TITLE},
            ).scalar_one()
        bind.execute(
            sa.text(
                "UPDATE documents SET conversation_id = :conversation_id WHERE user_id = :user_id"
            ),
            {"conversation_id": conversation_id, "user_id": user_id},
        )

    op.alter_column("documents", "conversation_id", nullable=False)
    op.create_foreign_key(
        "documents_conversation_id_fkey",
        "documents",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_documents_conversation_id", "documents", ["conversation_id"])


def downgrade() -> None:
    op.drop_column("documents", "conversation_id")
    op.drop_column("conversations", "auto_title")
