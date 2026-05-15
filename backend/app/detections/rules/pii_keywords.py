from __future__ import annotations

import re

from app.detections.contracts import NormalizedTelemetryEvent, RuleEvaluation, RuleHit
from app.detections.rules.base import DetectionRule

_PII_TERMS = (
    "social security",
    "ssn",
    "passport number",
    "driver's license",
    "drivers license",
    "credit card",
    "card number",
    "cvv",
    "bank account",
    "routing number",
    "hipaa",
    "phi",
    "patient id",
    "mrn",
    "salary",
    "compensation",
    "confidential",
    "restricted data",
    "classified",
    "nda",
    "source code",
    "api key",
    "private key",
)

_SSN_LIKE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_LIKE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


class PIIKeywordRule(DetectionRule):
    """Keyword and pattern hits (boosts when combined with AI tool matches in the engine)."""

    rule_id = "pii_keyword_v1"

    def evaluate(self, event: NormalizedTelemetryEvent) -> RuleEvaluation | None:
        hits: list[RuleHit] = []
        corpus = event.corpus
        for term in _PII_TERMS:
            if term in corpus:
                hits.append(
                    RuleHit(
                        rule_id=self.rule_id,
                        sub_type="keyword",
                        weight=12.0,
                        details={"term": term},
                    ),
                )
        if _SSN_LIKE.search(corpus):
            hits.append(
                RuleHit(
                    rule_id=self.rule_id,
                    sub_type="pattern_ssn_like",
                    weight=18.0,
                    details={"pattern": "ssn_like"},
                ),
            )
        if _CC_LIKE.search(corpus):
            hits.append(
                RuleHit(
                    rule_id=self.rule_id,
                    sub_type="pattern_numeric_blob",
                    weight=14.0,
                    details={"pattern": "numeric_sequence"},
                ),
            )
        hits = hits[:8]
        return RuleEvaluation(rule_id=self.rule_id, hits=hits) if hits else None
