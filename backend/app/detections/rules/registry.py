from __future__ import annotations

from app.detections.rules.ai_domains import AIToolDomainRule
from app.detections.rules.base import DetectionRule
from app.detections.rules.pii_keywords import PIIKeywordRule
from app.detections.rules.upload_heuristics import SuspiciousUploadRule


def default_ruleset() -> tuple[DetectionRule, ...]:
    """Ordered rules (domain first — downstream rules assume AI context)."""
    return (
        AIToolDomainRule(),
        SuspiciousUploadRule(),
        PIIKeywordRule(),
    )
