"""Data-access layer (SQLAlchemy)."""

from . import detection_repository
from . import report_repository

__all__ = ["detection_repository", "report_repository"]
