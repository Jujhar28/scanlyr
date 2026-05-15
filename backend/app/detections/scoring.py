from __future__ import annotations

from app.detections.contracts import RuleEvaluation
from app.models.enums import DetectionSeverity


def sum_rule_weights(evaluations: list[RuleEvaluation]) -> float:
    total = 0.0
    for ev in evaluations:
        for h in ev.hits:
            total += h.weight
    return min(100.0, total)


def numeric_to_severity(score: float) -> str:
    if score >= 88:
        return DetectionSeverity.critical.value
    if score >= 72:
        return DetectionSeverity.high.value
    if score >= 48:
        return DetectionSeverity.medium.value
    if score >= 28:
        return DetectionSeverity.low.value
    return DetectionSeverity.info.value


def confidence_from_score(score: float, hit_count: int) -> float:
    """Bounded heuristic confidence for rule-only mode (0–1)."""
    base = min(1.0, score / 100.0)
    boost = min(0.15, 0.02 * max(0, hit_count - 1))
    return round(min(1.0, base + boost), 3)
