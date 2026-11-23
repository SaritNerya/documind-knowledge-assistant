"""users.display_name: an optional, editable display name

Nullable, so existing users need no backfill. Safe to run again.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "display_name" not in columns:
        op.add_column("users", sa.Column("display_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "display_name")
