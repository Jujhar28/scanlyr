from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    memberships = relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    scan_sessions_started = relationship(
        "ScanSession",
        back_populates="started_by",
        foreign_keys="ScanSession.started_by_user_id",
    )
    detection_events = relationship(
        "AIDetectionEvent",
        back_populates="user",
        foreign_keys="AIDetectionEvent.user_id",
    )
    security_text_scans = relationship(
        "SecurityTextScan",
        back_populates="user",
        foreign_keys="SecurityTextScan.user_id",
    )
    reports_created = relationship(
        "Report",
        back_populates="created_by",
        foreign_keys="Report.created_by_user_id",
    )
    audit_logs_as_actor = relationship(
        "AuditLog",
        back_populates="actor_user",
        foreign_keys="AuditLog.actor_user_id",
    )
