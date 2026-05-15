"""Database session stub."""
from collections.abc import Generator
from unittest.mock import MagicMock

from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """Yield a database session. Stub for testing."""
    yield MagicMock(spec=Session)