"""conversations: multiple conversations per user, and a separate question usage log

1. Creates conversations and question_usage.
2. For every user who has messages: creates one conversation called
   "שיחה קודמת" and attaches all of that user's messages to it.
3. Copies existing user questions into question_usage, so today's quota
   stays correct right after the migration.
4. Makes messages.conversation_id NOT NULL and drops messages.user_id.

Safe to run again: each step checks the current schema first, and the
whole migration runs in one transaction (see env.py).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

LEGACY_TITLE = "שיחה קודמת"


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "conversations" not in existing:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    if "question_usage" not in existing:
        op.create_table(
            "question_usage",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index(
            "ix_question_usage_user_id_created_at", "question_usage", ["user_id", "created_at"]
        )

    columns = _columns("messages")
    if "user_id" not in columns:
        return  # ההודעות כבר במבנה החדש

    if "conversation_id" not in columns:
        op.add_column("messages", sa.Column("conversation_id", sa.Integer(), nullable=True))

    # שיחה "שיחה קודמת" אחת לכל משתמש שיש לו הודעות שעדיין לא שויכו
    owners = bind.execute(sa.text(
        "SELECT user_id, MIN(created_at), MAX(created_at) FROM messages "
        "WHERE conversation_id IS NULL GROUP BY user_id"
    )).all()
    for user_id, first_at, last_at in owners:
        conversation_id = bind.execute(
            sa.text(
                "INSERT INTO conversations (user_id, title, created_at, updated_at) "
                "VALUES (:user_id, :title, :created_at, :updated_at) RETURNING id"
            ),
            {"user_id": user_id, "title": LEGACY_TITLE, "created_at": first_at, "updated_at": last_at},
        ).scalar_one()
        bind.execute(
            sa.text(
                "UPDATE messages SET conversation_id = :conversation_id "
                "WHERE user_id = :user_id AND conversation_id IS NULL"
            ),
            {"conversation_id": conversation_id, "user_id": user_id},
        )

    # השאלות הקיימות נכנסות ליומן השימוש, כדי שהמכסה היומית תמשיך להיספר נכון
    bind.execute(sa.text(
        "INSERT INTO question_usage (user_id, created_at) "
        "SELECT user_id, created_at FROM messages WHERE role = 'user'"
    ))

    op.alter_column("messages", "conversation_id", nullable=False)
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    # מחיקת העמודה מוחקת איתה גם את האינדקס ואת ה-FK שלה
    op.drop_column("messages", "user_id")


def downgrade() -> None:
    # מחזיר את user_id מתוך הבעלים של השיחה. כל השיחות של משתמש מתאחדות שוב לרצף אחד.
    op.add_column("messages", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE messages m SET user_id = c.user_id FROM conversations c "
        "WHERE m.conversation_id = c.id"
    )
    op.alter_column("messages", "user_id", nullable=False)
    op.create_foreign_key(
        "messages_user_id_fkey", "messages", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_messages_user_id", "messages", ["user_id"])
    op.drop_column("messages", "conversation_id")
    op.drop_table("question_usage")
    op.drop_table("conversations")
