from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class UnsafePythonDetector(PatternListDetector):
    detector_id = "unsafe_python"
    default_finding_type = "unsafe_code"
    default_category = "code_execution"
    default_risk_category = "code_execution"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"\bexec\s*\("),
                "critical",
                "Python exec() usage",
                "Dynamic code execution via exec(): «{matched}».",
                "Never execute user-supplied Python; use sandboxed interpreters.",
            ),
            PatternSpec(
                re.compile(r"\beval\s*\("),
                "critical",
                "Python eval() usage",
                "eval() can execute arbitrary expressions: «{matched}».",
                "Replace eval with safe parsers (ast.literal_eval for data only).",
            ),
            PatternSpec(
                re.compile(r"__import__\s*\("),
                "high",
                "Dynamic import",
                "Dynamic __import__ detected: «{matched}».",
                "Restrict imports to an allow-list in code execution environments.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bos\.system\s*\("),
                "critical",
                "os.system call",
                "os.system invokes a shell: «{matched}».",
                "Use subprocess with shell=False and fixed argument lists.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bsubprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True"),
                "high",
                "Subprocess with shell=True",
                "subprocess with shell=True enables injection: «{matched}».",
                "Set shell=False and pass arguments as a sequence.",
            ),
        )
