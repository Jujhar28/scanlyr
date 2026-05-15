from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from app.detections.contracts import DetectionCandidate, NormalizedTelemetryEvent, RuleEvaluation, RuleHit
from app.detections.rules.registry import default_ruleset
from app.detections.scoring import (
    confidence_from_score,
    numeric_to_severity,
    sum_rule_weights,
)

if TYPE_CHECKING:
    from app.detections.rules.base import MLDetector


def _scale_evaluation(ev: RuleEvaluation, factor: float) -> RuleEvaluation:
    scaled = [
        RuleHit(
            rule_id=h.rule_id,
            sub_type=h.sub_type,
            weight=round(h.weight * factor, 3),
            details=h.details,
        )
        for h in ev.hits
    ]
    return RuleEvaluation(rule_id=ev.rule_id, hits=scaled)


def _tool_meta(slug: str) -> tuple[str, str | None]:
    from app.detections.rules.ai_domains import TOOL_BY_SLUG

    spec = TOOL_BY_SLUG.get(slug)
    if spec is None:
        return slug.replace("_", " ").title(), None
    return spec.display_name, spec.vendor


def run_rule_engine(
    event: NormalizedTelemetryEvent,
    *,
    ml_detector: MLDetector | None = None,
) -> list[DetectionCandidate]:
    """
    Execute modular rules. Domain hits fan out to one candidate per tool; upload/PII layers apply once.
    Optional ``ml_detector`` post-processes candidates for future ML enrichment.
    """
    rules = default_ruleset()
    domain_ev = rules[0].evaluate(event)
    if domain_ev is None or not domain_ev.hits:
        return []

    upload_ev = rules[1].evaluate(event)
    pii_ev = rules[2].evaluate(event)

    n_tools = max(1, len(domain_ev.hits))
    factor = 1.0 / n_tools
    shared: list[RuleEvaluation] = []
    if upload_ev is not None and upload_ev.hits:
        shared.append(_scale_evaluation(upload_ev, factor))
    if pii_ev is not None and pii_ev.hits:
        shared.append(_scale_evaluation(pii_ev, factor))

    candidates: list[DetectionCandidate] = []

    for hit in domain_ev.hits:
        slug = hit.sub_type
        tool_name, vendor = _tool_meta(slug)
        per_tool_domain = RuleEvaluation(rule_id=domain_ev.rule_id, hits=[hit])
        evaluations = [per_tool_domain, *shared]
        score = sum_rule_weights(evaluations)
        severity = numeric_to_severity(score)
        hit_count = sum(len(e.hits) for e in evaluations)
        confidence = confidence_from_score(score, hit_count)

        dedupe_raw = f"{event.organization_id}|{event.source}|{event.graph_item_id}|{slug}"
        dedupe_key = hashlib.sha256(dedupe_raw.encode("utf-8")).hexdigest()

        external_ref = f"{event.source}:{event.graph_item_id}"

        evidence = {
            "graph_item_id": event.graph_item_id,
            "source": event.source,
            "actor_hint": event.actor_hint,
            "rules": [
                {
                    "rule_id": e.rule_id,
                    "hits": [
                        {
                            "sub_type": h.sub_type,
                            "weight": h.weight,
                            "details": h.details,
                        }
                        for h in e.hits
                    ],
                }
                for e in evaluations
            ],
            "raw_snapshot": event.raw_snapshot,
        }

        candidates.append(
            DetectionCandidate(
                tool_slug=slug,
                tool_name=tool_name,
                tool_vendor=vendor,
                channel=event.source,
                dedupe_key=dedupe_key,
                occurred_at=event.occurred_at,
                external_ref=external_ref[:1024],
                evaluations=evaluations,
                evidence=evidence,
                numeric_score=score,
                severity=severity,
                confidence=confidence,
            ),
        )

    if ml_detector is not None:
        candidates = ml_detector.enrich(event, candidates)

    return candidates


def run_engine_on_events(
    events: list[NormalizedTelemetryEvent],
    *,
    ml_detector: MLDetector | None = None,
) -> list[DetectionCandidate]:
    out: list[DetectionCandidate] = []
    for ev in events:
        out.extend(run_rule_engine(ev, ml_detector=ml_detector))
    return out
