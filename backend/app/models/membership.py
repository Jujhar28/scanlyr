"""Membership ORM model stub — minimal SQLAlchemy mapping for testing."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("roles.id"), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)