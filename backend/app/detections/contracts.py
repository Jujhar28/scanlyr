from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NormalizedTelemetryEvent:
    """Canonical input for the rules engine (vendor-agnostic, ML-ready)."""

    organization_id: uuid.UUID
    source: str
    graph_item_id: str
    occurred_at: datetime
    corpus: str
    raw_snapshot: dict[str, Any]
    actor_hint: str | None = None


@dataclass
class RuleHit:
    rule_id: str
    sub_type: str
    weight: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleEvaluation:
    rule_id: str
    hits: list[RuleHit] = field(default_factory=list)


@dataclass
class DetectionCandidate:
    """One persisted finding: a specific AI tool (or vendor bucket) on one telemetry row."""

    tool_slug: str
    tool_name: str
    tool_vendor: str | None
    channel: str
    dedupe_key: str
    occurred_at: datetime
    external_ref: str
    evaluations: list[RuleEvaluation]
    evidence: dict[str, Any]
    numeric_score: float
    severity: str
    confidence: float
