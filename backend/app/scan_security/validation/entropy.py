"""Entropy helpers for secret-like material detection."""

from __future__ import annotations

import math
import re
from collections import Counter

_PLACEHOLDER_RE = re.compile(
    r"(?i)^(x{3,}|test|demo|sample|example|placeholder|redacted|null|none|"
    r"your[_-]?password|hunter2|changeme|password123|secret|dummy|fake|"
    r"insert[_-]?here|\*{3,}|<[^>]+>|\[redacted\])$",
)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def is_placeholder_value(value: str) -> bool:
    cleaned = value.strip().strip("\"'")
    if len(cleaned) < 4:
        return True
    return bool(_PLACEHOLDER_RE.match(cleaned))


def looks_like_secret_material(value: str, *, min_length: int = 12) -> bool:
    """Heuristic: high-entropy alphanumeric secret (not a dictionary word)."""
    cleaned = value.strip().strip("\"'")
    if len(cleaned) < min_length:
        return False
    if is_placeholder_value(cleaned):
        return False
    if cleaned.isalpha() and cleaned.islower() and len(cleaned) < 20:
        return False
    entropy = shannon_entropy(cleaned)
    if len(cleaned) >= 24:
        return entropy >= 3.2
    return entropy >= 3.8
