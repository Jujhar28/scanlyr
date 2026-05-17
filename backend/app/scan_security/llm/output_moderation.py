from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class OutputModerationDetector(PatternListDetector):
    """Moderation checks for harmful or policy-violating model outputs."""

    detector_id = "llm_output_moderation"
    default_finding_type = "output_moderation"
    default_category = "moderation"
    default_risk_category = "output_moderation"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "output"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)\b(here\s+is\s+how\s+to|step\s+1:)\s+.*(harm|kill|attack|hack)",
                ),
                "critical",
                "Harmful procedural output",
                "Model output appears to provide harmful procedural guidance: «{matched}».",
                "Block completion before delivery; regenerate with safety system prompt.",
                risk_category="output_moderation",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(i\s+cannot|i\s+can't)\s+help\s+with\s+that\b"),
                "low",
                "Safety refusal present",
                "Model issued a safety refusal (expected for blocked requests): «{matched}».",
                "No action required; log for audit trail.",
                risk_category="output_moderation",
            ),
            PatternSpec(
                re.compile(
                    r"(?i)\b(explicit|graphic)\s+(sexual|violent)\s+(content|description)",
                ),
                "high",
                "Explicit content flag",
                "Output references explicit prohibited content: «{matched}».",
                "Apply content filter on assistant messages before display.",
                risk_category="output_moderation",
            ),
            PatternSpec(
                re.compile(r"(?i)\bself[- ]?harm\s+(instructions|methods)\b"),
                "critical",
                "Self-harm content",
                "Self-harm related content in output: «{matched}».",
                "Escalate per crisis policy; do not render to end users.",
                risk_category="output_moderation",
            ),
        )
