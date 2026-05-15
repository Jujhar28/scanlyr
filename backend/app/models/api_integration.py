from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import IntegrationStatus
from app.models.mixins import TenantMixin, TimestampMixin


class APIIntegration(Base, TenantMixin, TimestampMixin):
    """Outbound or inbound integration configuration (secrets live outside the DB)."""

    __tablename__ = "api_integrations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "integration_key",
            name="uq_api_integrations_org_integration_key",
        ),
        Index("ix_api_integrations_org_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    integration_key: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=IntegrationStatus.active.value,
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="api_integrations")
