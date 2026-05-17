from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class UnsafeInstructionsDetector(PatternListDetector):
    """Detects harmful or policy-violating instructions in prompts."""

    detector_id = "llm_unsafe_instructions"
    default_finding_type = "unsafe_instructions"
    default_category = "unsafe_instruction"
    default_risk_category = "unsafe_instructions"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)\b(how\s+to|steps\s+to)\s+(make|build|synthesize)\s+(a\s+)?(bomb|weapon|malware)",
                ),
                "critical",
                "Weapons or malware instructions",
                "Instruction to create weapons or malware: «{matched}».",
                "Refuse harmful instruction requests; escalate per abuse policy.",
                risk_category="unsafe_instructions",
            ),
            PatternSpec(
                re.compile(r"(?i)\bsteal\s+(credentials|cookies|session|tokens?)\b"),
                "critical",
                "Credential theft instruction",
                "Instruction targeting credential theft: «{matched}».",
                "Block and alert on credential theft phrasing in agent prompts.",
                risk_category="unsafe_instructions",
            ),
            PatternSpec(
                re.compile(r"(?i)\bbypass\s+(authentication|2fa|mfa|login)\b"),
                "high",
                "Auth bypass instruction",
                "Authentication bypass requested: «{matched}».",
                "Do not assist with security control circumvention.",
                risk_category="unsafe_instructions",
            ),
        )
