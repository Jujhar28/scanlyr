from __future__ import annotations

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OrganizationStatus
from app.models.mixins import TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OrganizationStatus.active.value,
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    roles = relationship(
        "Role",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    memberships = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    scan_sessions = relationship(
        "ScanSession",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    detection_events = relationship(
        "AIDetectionEvent",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    security_text_scans = relationship(
        "SecurityTextScan",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    risk_scores = relationship(
        "RiskScore",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    reports = relationship(
        "Report",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="organization",
    )
    api_integrations = relationship(
        "APIIntegration",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    microsoft_graph_connection = relationship(
        "MicrosoftGraphConnection",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
