from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DetectionSeverity
from app.models.mixins import TenantMixin, TimestampMixin


class AIDetectionEvent(Base, TenantMixin, TimestampMixin):
    """Normalized Shadow AI signal (tool, channel, evidence metadata)."""

    __tablename__ = "ai_detection_events"
    __table_args__ = (
        Index("ix_ai_detection_events_org_occurred_at", "organization_id", "occurred_at"),
        Index("ix_ai_detection_events_scan_session_id", "scan_session_id"),
        Index("ix_ai_detection_events_org_severity", "organization_id", "severity"),
        UniqueConstraint(
            "organization_id",
            "dedupe_key",
            name="uq_ai_detection_events_org_dedupe_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scan_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DetectionSeverity.medium.value,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(512), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="detection_events")
    scan_session = relationship("ScanSession", back_populates="detection_events")
    risk_scores = relationship(
        "RiskScore",
        back_populates="detection_event",
        cascade="all, delete-orphan",
    )
