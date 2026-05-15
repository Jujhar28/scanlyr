from __future__ import annotations

from app.detections.contracts import DetectionCandidate, NormalizedTelemetryEvent


class NullMLDetector:
    """Placeholder until a model registry wires real inference."""

    def enrich(
        self,
        _event: NormalizedTelemetryEvent,
        candidates: list[DetectionCandidate],
    ) -> list[DetectionCandidate]:
        return candidates
