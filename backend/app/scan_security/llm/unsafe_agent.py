from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class UnsafeAgentActionDetector(PatternListDetector):
    """Detects dangerous tool/agent actions in prompts (file, network, code)."""

    detector_id = "llm_unsafe_agent"
    default_finding_type = "unsafe_agent"
    default_category = "agent_action"
    default_risk_category = "unsafe_agent_action"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\b(function_call|tool_use|invoke_tool)\s*[\({]"),
                "high",
                "Tool invocation syntax",
                "Structured tool/agent invocation detected: «{matched}».",
                "Allow-list tools per tenant; require human approval for destructive actions.",
                risk_category="unsafe_agent_action",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(delete|remove|wipe)\s+(all\s+)?(files?|database|bucket|repo)"),
                "critical",
                "Destructive resource action",
                "Destructive delete operation requested: «{matched}».",
                "Require step-up auth and dry-run previews for destructive tools.",
                risk_category="unsafe_agent_action",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(send_email|post_message|slack_message)\s*\("),
                "high",
                "Outbound messaging action",
                "Agent messaging action detected: «{matched}».",
                "Rate-limit outbound comms; scan content before send.",
                risk_category="unsafe_agent_action",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(browse_url|fetch_url|web_search)\s*\([^)]*http"),
                "medium",
                "Unrestricted web fetch",
                "Agent web fetch to arbitrary URL: «{matched}».",
                "Restrict egress to approved domains and sanitize fetched HTML.",
                risk_category="unsafe_agent_action",
            ),
            PatternSpec(
                re.compile(r"(?i)\brun_code\s*\(|execute_python\s*\("),
                "critical",
                "Arbitrary code execution",
                "Agent code execution call detected: «{matched}».",
                "Sandbox code tools with timeouts, no network, and read-only FS.",
                risk_category="unsafe_agent_action",
            ),
        )
