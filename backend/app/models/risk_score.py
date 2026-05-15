from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TenantMixin, TimestampMixin


class RiskScore(Base, TenantMixin, TimestampMixin):
    """Quantified risk for a detection, a scan session aggregate, or org-wide rollups."""

    __tablename__ = "risk_scores"
    __table_args__ = (
        CheckConstraint(
            "(score_kind = 'detection' AND ai_detection_event_id IS NOT NULL AND scan_session_id IS NULL) "
            "OR (score_kind = 'session' AND scan_session_id IS NOT NULL AND ai_detection_event_id IS NULL) "
            "OR (score_kind = 'organization' AND ai_detection_event_id IS NULL AND scan_session_id IS NULL)",
            name="ck_risk_scores_subject_consistency",
        ),
        Index("ix_risk_scores_org_computed_at", "organization_id", "computed_at"),
        Index("ix_risk_scores_detection_event_id", "ai_detection_event_id"),
        Index("ix_risk_scores_scan_session_id", "scan_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    score_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_detection_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_detection_events.id", ondelete="CASCADE"),
        nullable=True,
    )
    scan_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scan_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    factors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="risk_scores")
    detection_event = relationship("AIDetectionEvent", back_populates="risk_scores")
    scan_session = relationship("ScanSession", back_populates="risk_scores")
