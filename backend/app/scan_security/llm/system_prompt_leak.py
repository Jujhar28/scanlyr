from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SystemPromptLeakageDetector(PatternListDetector):
    """Detects attempts to extract system prompts or hidden instructions."""

    detector_id = "llm_system_prompt_leak"
    default_finding_type = "system_prompt_leak"
    default_category = "system_prompt"
    default_risk_category = "system_prompt_leakage"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)\b(repeat|print|reveal|show|dump)\s+(your\s+)?(system\s+)?(prompt|instructions)",
                ),
                "high",
                "System prompt exfiltration",
                "Request to disclose system or hidden instructions: «{matched}».",
                "Never echo system prompts; return a generic refusal.",
                risk_category="system_prompt_leakage",
            ),
            PatternSpec(
                re.compile(r"(?i)\bwhat\s+(are|were)\s+your\s+(original\s+)?instructions\b"),
                "high",
                "Instruction probing",
                "Probing for original model instructions: «{matched}».",
                "Use output filters to block instruction replay.",
                risk_category="system_prompt_leakage",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(begin\s+system\s+prompt|```\s*system)"),
                "medium",
                "System block delimiter",
                "Markers suggesting system prompt boundaries: «{matched}».",
                "Strip delimiter tokens from user input before model invocation.",
                risk_category="system_prompt_leakage",
            ),
        )
