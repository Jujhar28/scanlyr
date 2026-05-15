"""shadow AI detection tables (scan sessions, AI events, risk scores)

Revision ID: 0005_shadow_ai_detection
Revises: 0004_microsoft_graph
Create Date: 2026-05-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_shadow_ai_detection"
down_revision: str | Sequence[str] | None = "0004_microsoft_graph"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("scan_type", sa.String(length=64), nullable=False, server_default="scheduled"),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["started_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_scan_sessions_org_started_at", "scan_sessions", ["organization_id", "started_at"])
    op.create_index("ix_scan_sessions_org_status", "scan_sessions", ["organization_id", "status"])

    op.create_table(
        "ai_detection_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=True),
        sa.Column("tool_vendor", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("external_ref", sa.String(length=1024), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["scan_session_id"], ["scan_sessions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_ai_detection_events_org_dedupe_key"),
    )
    op.create_index(
        "ix_ai_detection_events_org_occurred_at",
        "ai_detection_events",
        ["organization_id", "occurred_at"],
    )
    op.create_index("ix_ai_detection_events_scan_session_id", "ai_detection_events", ["scan_session_id"])
    op.create_index(
        "ix_ai_detection_events_org_severity",
        "ai_detection_events",
        ["organization_id", "severity"],
    )

    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score_kind", sa.String(length=32), nullable=False),
        sa.Column("ai_detection_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scan_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score", sa.Numeric(6, 3), nullable=False),
        sa.Column("factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False, server_default="v1"),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "(score_kind = 'detection' AND ai_detection_event_id IS NOT NULL AND scan_session_id IS NULL) "
            "OR (score_kind = 'session' AND scan_session_id IS NOT NULL AND ai_detection_event_id IS NULL) "
            "OR (score_kind = 'organization' AND ai_detection_event_id IS NULL AND scan_session_id IS NULL)",
            name="ck_risk_scores_subject_consistency",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_detection_event_id"], ["ai_detection_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_session_id"], ["scan_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_risk_scores_org_computed_at", "risk_scores", ["organization_id", "computed_at"])
    op.create_index("ix_risk_scores_detection_event_id", "risk_scores", ["ai_detection_event_id"])
    op.create_index("ix_risk_scores_scan_session_id", "risk_scores", ["scan_session_id"])


def downgrade() -> None:
    op.drop_index("ix_risk_scores_scan_session_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_detection_event_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_org_computed_at", table_name="risk_scores")
    op.drop_table("risk_scores")
    op.drop_index("ix_ai_detection_events_org_severity", table_name="ai_detection_events")
    op.drop_index("ix_ai_detection_events_scan_session_id", table_name="ai_detection_events")
    op.drop_index("ix_ai_detection_events_org_occurred_at", table_name="ai_detection_events")
    op.drop_table("ai_detection_events")
    op.drop_index("ix_scan_sessions_org_status", table_name="scan_sessions")
    op.drop_index("ix_scan_sessions_org_started_at", table_name="scan_sessions")
    op.drop_table("scan_sessions")
