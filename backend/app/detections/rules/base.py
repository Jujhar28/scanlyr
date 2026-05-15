from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.detections.contracts import DetectionCandidate, NormalizedTelemetryEvent


@runtime_checkable
class DetectionRule(Protocol):
    rule_id: str

    def evaluate(self, event: NormalizedTelemetryEvent) -> object | None:
        """Return RuleEvaluation or None."""


@runtime_checkable
class MLDetector(Protocol):
    """Future hook for ONNX / remote models — keep contracts stable."""

    def enrich(
        self,
        event: NormalizedTelemetryEvent,
        candidates: list[DetectionCandidate],
    ) -> list[DetectionCandidate]:
        ...
