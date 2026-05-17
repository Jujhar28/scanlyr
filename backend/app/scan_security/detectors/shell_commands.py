from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SuspiciousShellCommandDetector(PatternListDetector):
    detector_id = "suspicious_shell"
    default_finding_type = "shell_command"
    default_category = "execution"
    default_risk_category = "unsafe_agent_action"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\bcurl\b[^\n|]*\|\s*(ba)?sh\b"),
                "critical",
                "Curl pipe to shell",
                "Remote script fetch piped into a shell: «{matched}».",
                "Block curl|bash patterns in agent tools; verify script provenance.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bwget\b[^\n|]*\|\s*(ba)?sh\b"),
                "critical",
                "Wget pipe to shell",
                "wget piped to shell execution: «{matched}».",
                "Disallow piping downloaded content directly into interpreters.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bchmod\s+\+x\b"),
                "medium",
                "Make-executable command",
                "chmod +x usage detected: «{matched}».",
                "Review whether binaries should be made executable from user-supplied paths.",
            ),
            PatternSpec(
                re.compile(r"(?i)(/bin/(ba)?sh|cmd\.exe|powershell\.exe)"),
                "medium",
                "Shell interpreter invocation",
                "Direct shell interpreter reference: «{matched}».",
                "Restrict agents to safe APIs instead of spawning shells.",
            ),
        )
