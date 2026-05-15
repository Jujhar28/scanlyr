"""Security utilities stub."""
from __future__ import annotations

from typing import Any


def safe_decode_access_token(token: str) -> dict[str, Any] | None:
    """Return claims or None on any decode/verify failure."""
    return None