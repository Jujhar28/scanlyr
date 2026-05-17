"""add user_id to ai_detection_events

Revision ID: 0008_ai_detection_events_user_id
Revises: 0007_audit_logs
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_ai_detection_events_user_id"
down_revision: str | Sequence[str] | None = "0007_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ai_detection_events",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ai_detection_events_user_id_users",
        "ai_detection_events",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ai_detection_events_user_id", "ai_detection_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_detection_events_user_id", table_name="ai_detection_events")
    op.drop_constraint(
        "fk_ai_detection_events_user_id_users",
        "ai_detection_events",
        type_="foreignkey",
    )
    op.drop_column("ai_detection_events", "user_id")
