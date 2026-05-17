"""security_text_scans table for scan history and analytics

Revision ID: 0009_security_text_scans
Revises: 0008_ai_detection_events_user_id
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_security_text_scans"
down_revision: str | Sequence[str] | None = "0008_ai_detection_events_user_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "security_text_scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detection_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(length=16), nullable=False, server_default="auto"),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("finding_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_preview", sa.Text(), nullable=False),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "engine_version",
            sa.String(length=64),
            nullable=False,
            server_default="scan_security_v3_llm",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["detection_event_id"],
            ["ai_detection_events.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_security_text_scans_org_scanned_at",
        "security_text_scans",
        ["organization_id", "scanned_at"],
    )
    op.create_index(
        "ix_security_text_scans_org_risk_level",
        "security_text_scans",
        ["organization_id", "risk_level"],
    )
    op.create_index(
        "ix_security_text_scans_org_user_id",
        "security_text_scans",
        ["organization_id", "user_id"],
    )
    op.create_index(
        "ix_security_text_scans_detection_event_id",
        "security_text_scans",
        ["detection_event_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_security_text_scans_detection_event_id", table_name="security_text_scans")
    op.drop_index("ix_security_text_scans_org_user_id", table_name="security_text_scans")
    op.drop_index("ix_security_text_scans_org_risk_level", table_name="security_text_scans")
    op.drop_index("ix_security_text_scans_org_scanned_at", table_name="security_text_scans")
    op.drop_table("security_text_scans")
