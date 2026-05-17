from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class JailbreakDetector(PatternListDetector):
    """Detects jailbreak and policy-bypass attempts in user prompts."""

    detector_id = "llm_jailbreak"
    default_finding_type = "jailbreak"
    default_category = "llm_jailbreak"
    default_risk_category = "jailbreak"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\b(dan|do\s+anything\s+now)\s+mode\b"),
                "critical",
                "DAN-style jailbreak",
                "Known 'Do Anything Now' jailbreak pattern: «{matched}».",
                "Block DAN/jailbreak phrases at the gateway; use fixed system prompts.",
                risk_category="jailbreak",
            ),
            PatternSpec(
                re.compile(r"(?i)\bact\s+as\s+(if\s+you\s+are|an?)\s+(unrestricted|evil|uncensored)"),
                "high",
                "Malicious role assignment",
                "User attempts to assign an unrestricted or harmful persona: «{matched}».",
                "Reject role overrides; keep assistant identity in system instructions only.",
                risk_category="jailbreak",
            ),
            PatternSpec(
                re.compile(r"(?i)\bno\s+(rules|restrictions|limits|guardrails)\b"),
                "high",
                "Guardrail removal request",
                "Explicit request to remove safety constraints: «{matched}».",
                "Log and rate-limit repeat offenders; enforce policy templates.",
                risk_category="jailbreak",
            ),
            PatternSpec(
                re.compile(r"(?i)\bhypothetically\s+ignore\s+(safety|policy|guidelines)"),
                "medium",
                "Hypothetical policy bypass",
                "Hypothetical framing to bypass safety: «{matched}».",
                "Treat hypothetical harmful requests as in-scope for refusal.",
                risk_category="jailbreak",
            ),
        )
