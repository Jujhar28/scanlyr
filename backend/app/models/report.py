from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReportStatus, ReportType
from app.models.mixins import TenantMixin, TimestampMixin


class Report(Base, TenantMixin, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_org_created_at", "organization_id", "created_at"),
        Index("ix_reports_org_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReportType.compliance.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReportStatus.draft.value,
    )
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="reports")
    created_by = relationship("User", foreign_keys=[created_by_user_id], back_populates="reports_created")
