from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SensitiveDataExposureDetector(PatternListDetector):
    """Detects PII and regulated data in prompts and model outputs."""

    detector_id = "llm_sensitive_data"
    default_finding_type = "sensitive_data"
    default_category = "pii"
    default_risk_category = "sensitive_data_exposure"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt", "output"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
                "critical",
                "SSN pattern",
                "US Social Security number pattern detected: «{matched}».",
                "Redact SSNs; block logging of raw PII in prompts and completions.",
                risk_category="sensitive_data_exposure",
            ),
            PatternSpec(
                re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
                "high",
                "Payment card pattern",
                "Credit/debit card number pattern detected: «{matched}».",
                "Tokenize PANs; comply with PCI-DSS handling requirements.",
                risk_category="sensitive_data_exposure",
            ),
            PatternSpec(
                re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
                "medium",
                "Email address",
                "Email address present in content: «{matched}».",
                "Minimize PII in model context; apply field-level encryption at rest.",
                risk_category="sensitive_data_exposure",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(diagnosis|medical\s+record|patient\s+id)\s*[:=]\s*\S+"),
                "high",
                "Health data reference",
                "Healthcare-related identifier or diagnosis reference: «{matched}».",
                "Treat as PHI under HIPAA policies; restrict model retention.",
                risk_category="sensitive_data_exposure",
            ),
        )
