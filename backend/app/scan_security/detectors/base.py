from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from app.scan_security.context import ContentKind, RiskCategory, ScanContext
from app.scan_security.schemas.findings import FindingType, SecurityFinding, Severity

_SEVERITY_CONFIDENCE: dict[Severity, float] = {
    "critical": 0.91,
    "high": 0.84,
    "medium": 0.72,
    "low": 0.58,
}


@dataclass(frozen=True)
class PatternSpec:
    """One regex rule with metadata for findings and scoring."""

    pattern: re.Pattern[str]
    severity: Severity
    title: str
    description: str
    remediation: str
    category: str | None = None
    risk_category: RiskCategory | None = None
    finding_type: FindingType | str | None = None
    confidence: float | None = None


class SecurityDetector(ABC):
    """Scalable detector interface — implement ``detect_with_context`` for new rules."""

    detector_id: str
    default_finding_type: FindingType | str
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt", "output"})

    def applies_to(self, context: ScanContext) -> bool:
        kind = context.content_kind
        if kind == "auto":
            return True
        return kind in self.supported_content

    def detect(self, text: str) -> list[SecurityFinding]:
        return self.detect_with_context(ScanContext(text=text, content_kind="auto"))

    @abstractmethod
    def detect_with_context(self, context: ScanContext) -> list[SecurityFinding]:
        ...


class PatternListDetector(SecurityDetector, ABC):
    """Base for regex-driven detectors; subclasses define ``detector_id`` and ``patterns``."""

    default_category: str
    default_risk_category: RiskCategory

    @property
    @abstractmethod
    def patterns(self) -> tuple[PatternSpec, ...]:
        ...

    def detect_with_context(self, context: ScanContext) -> list[SecurityFinding]:
        if not self.applies_to(context):
            return []
        return self._match_patterns(context.text)

    def _match_patterns(self, text: str) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        seen: set[str] = set()
        for spec in self.patterns:
            for match in spec.pattern.finditer(text):
                key = f"{spec.title}:{match.start()}"
                if key in seen:
                    continue
                seen.add(key)
                snippet = _safe_snippet(text, match.start(), match.end())
                matched_len = match.end() - match.start()
                findings.append(
                    SecurityFinding(
                        type=spec.finding_type or self.default_finding_type,
                        detector_id=self.detector_id,
                        category=spec.category or self.default_category,
                        risk_category=spec.risk_category or self.default_risk_category,
                        severity=spec.severity,
                        title=spec.title,
                        description=spec.description.format(matched=snippet or "(redacted)"),
                        remediation=spec.remediation,
                        confidence=_confidence_for_match(spec, matched_len),
                        evidence={
                            "start": match.start(),
                            "end": match.end(),
                            "pattern": spec.pattern.pattern,
                        },
                    ),
                )
        return findings


def _confidence_for_match(spec: PatternSpec, matched_len: int) -> float:
    base = spec.confidence if spec.confidence is not None else _SEVERITY_CONFIDENCE[spec.severity]
    boost = min(0.06, matched_len / 200.0)
    return round(min(0.99, base + boost), 3)


def _safe_snippet(text: str, start: int, end: int, *, max_len: int = 48) -> str:
    raw = text[start:end].replace("\n", " ").strip()
    if len(raw) <= max_len:
        return raw
    return raw[: max_len - 3] + "..."
