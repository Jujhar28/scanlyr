from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TenantMixin, TimestampMixin


class SecurityTextScan(Base, TenantMixin, TimestampMixin):
    """Persisted security text scan for history, filtering, and org analytics."""

    __tablename__ = "security_text_scans"
    __table_args__ = (
        Index("ix_security_text_scans_org_scanned_at", "organization_id", "scanned_at"),
        Index("ix_security_text_scans_org_risk_level", "organization_id", "risk_level"),
        Index("ix_security_text_scans_org_user_id", "organization_id", "user_id"),
        Index("ix_security_text_scans_detection_event_id", "detection_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    detection_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_detection_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(16), nullable=False, default="auto")
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_preview: Mapped[str] = mapped_column(Text, nullable=False)
    result_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False, default="scan_security_v3_llm")

    organization = relationship("Organization", back_populates="security_text_scans")
    user = relationship("User", back_populates="security_text_scans", foreign_keys=[user_id])
    detection_event = relationship("AIDetectionEvent", foreign_keys=[detection_event_id])
