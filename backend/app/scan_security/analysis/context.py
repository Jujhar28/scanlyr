"""Benign-context and discourse signals to reduce false positives."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.scan_security.analysis.fixtures import _FIXTURE_DISCOURSE

_BENIGN_DISCUSSION = re.compile(
    r"(?i)\b("
    r"security\s+policy|best\s+practice|for\s+example|e\.g\.|such\s+as|"
    r"do\s+not\s+share|never\s+share|avoid\s+sharing|training|documentation|"
    r"quarterly\s+report|hello\s+world|sample\s+text|test\s+case|"
    r"reset\s+(?:your|my)\s+password|forgot\s+password|password\s+reset|"
    r"test\s+user|test\s+account|example\s+only|not\s+real|dummy\s+data"
    r")\b",
)

_QUOTED_EXAMPLE = re.compile(
    r"(?i)(example|sample|demo|test)\s+(password|key|token|secret|user|account|email)",
)

_CODE_FENCE = re.compile(r"```[\s\S]*?```")

_TEST_EMAIL_IN_TEXT = re.compile(
    r"(?i)\b(?:test|user|demo|sample|admin)@[a-z0-9.-]+\.[a-z]{2,}\b",
)


@dataclass(frozen=True)
class TextContextProfile:
    """Signals derived from full input text (not per-match)."""

    length: int
    benign_discussion_hits: int
    has_code_fence: bool
    placeholder_density: float
    benign_score: float
    has_synthetic_fixture_discourse: bool

    @property
    def is_mostly_benign(self) -> bool:
        return self.benign_score >= 0.55

    @property
    def is_likely_fixture(self) -> bool:
        """Strong hint that content is QA / docs / training material."""
        return self.has_synthetic_fixture_discourse or self.benign_score >= 0.65

    @property
    def risk_dampening(self) -> float:
        """Multiplier applied to aggregate risk score (0.5–1.0)."""
        if self.benign_score >= 0.7:
            return 0.5
        if self.benign_score >= 0.55:
            return 0.62
        if self.benign_score >= 0.45:
            return 0.72
        if self.benign_score >= 0.25:
            return 0.88
        return 1.0


def analyze_text_context(text: str) -> TextContextProfile:
    stripped = text.strip()
    length = len(stripped)
    benign_hits = len(_BENIGN_DISCUSSION.findall(stripped)) + len(_QUOTED_EXAMPLE.findall(stripped))
    has_fence = bool(_CODE_FENCE.search(stripped))
    fixture_discourse = bool(_FIXTURE_DISCOURSE.search(stripped)) or bool(
        _TEST_EMAIL_IN_TEXT.search(stripped),
    )

    placeholder_tokens = len(
        re.findall(
            r"(?i)\b(test|demo|example|sample|placeholder|xxx+|hunter2|changeme|password123)\b",
            stripped,
        ),
    )
    word_count = max(1, len(stripped.split()))
    placeholder_density = min(1.0, placeholder_tokens / word_count)

    raw_benign = (
        0.12 * min(4, benign_hits)
        + 0.15 * (1.0 if has_fence else 0.0)
        + 0.35 * placeholder_density
        + (0.2 if length < 80 and benign_hits else 0.0)
        + (0.25 if fixture_discourse else 0.0)
        + (0.15 if _TEST_EMAIL_IN_TEXT.search(stripped) else 0.0)
    )
    benign_score = min(1.0, raw_benign)

    return TextContextProfile(
        length=length,
        benign_discussion_hits=benign_hits,
        has_code_fence=has_fence,
        placeholder_density=placeholder_density,
        benign_score=benign_score,
        has_synthetic_fixture_discourse=fixture_discourse,
    )
