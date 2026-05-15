from __future__ import annotations

import re

from app.detections.contracts import NormalizedTelemetryEvent, RuleEvaluation, RuleHit
from app.detections.rules.base import DetectionRule

_UPLOAD_RE = re.compile(
    r"\b("
    r"upload|uploaded|uploading|attachment|attached file|file attached|"
    r"shared (a )?file|paste(d)?|clipboard|onedrive|sharepoint|"
    r"sent (an? )?attachment|exfil|export(ed)?"
    r")\b",
    re.IGNORECASE,
)


class SuspiciousUploadRule(DetectionRule):
    """Elevate risk when AI-related context co-occurs with upload / exfil language."""

    rule_id = "suspicious_upload_v1"

    def evaluate(self, event: NormalizedTelemetryEvent) -> RuleEvaluation | None:
        if not _UPLOAD_RE.search(event.corpus):
            return None
        hits: list[RuleHit] = []
        for m in _UPLOAD_RE.finditer(event.corpus):
            token = m.group(0)
            hits.append(
                RuleHit(
                    rule_id=self.rule_id,
                    sub_type="upload_language",
                    weight=22.0,
                    details={"token": token},
                ),
            )
            break
        return RuleEvaluation(rule_id=self.rule_id, hits=hits) if hits else None
