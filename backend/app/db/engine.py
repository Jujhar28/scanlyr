"""SQLAlchemy engine factory (PostgreSQL / psycopg v3)."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import Settings, settings


def create_engine_from_settings(cfg: Settings) -> Engine:
    """Create a sync engine suitable for web workers (Alembic uses NullPool separately)."""
    return create_engine(
        cfg.database_url,
        pool_pre_ping=cfg.db_pool_pre_ping,
        pool_size=cfg.db_pool_size,
        max_overflow=cfg.db_max_overflow,
        pool_timeout=cfg.db_pool_timeout,
        pool_recycle=cfg.db_pool_recycle,
        echo=cfg.database_echo,
        future=True,
    )


engine = create_engine_from_settings(settings)

__all__ = ["create_engine_from_settings", "engine"]
