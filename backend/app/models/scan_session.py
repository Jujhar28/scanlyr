from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ScanSessionStatus
from app.models.mixins import TenantMixin, TimestampMixin


class ScanSession(Base, TenantMixin, TimestampMixin):
    """A bounded run of collection / analysis that groups detection events."""

    __tablename__ = "scan_sessions"
    __table_args__ = (
        Index("ix_scan_sessions_org_started_at", "organization_id", "started_at"),
        Index("ix_scan_sessions_org_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    started_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ScanSessionStatus.queued.value,
    )
    scan_type: Mapped[str] = mapped_column(String(64), nullable=False, default="scheduled")
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="scan_sessions")
    started_by = relationship("User", foreign_keys=[started_by_user_id], back_populates="scan_sessions_started")
    detection_events = relationship(
        "AIDetectionEvent",
        back_populates="scan_session",
        cascade="all, delete-orphan",
    )
    risk_scores = relationship(
        "RiskScore",
        back_populates="scan_session",
        cascade="all, delete-orphan",
    )
