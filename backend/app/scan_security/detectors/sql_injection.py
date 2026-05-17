from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SqlInjectionDetector(PatternListDetector):
    detector_id = "sql_injection"
    default_finding_type = "sql_injection"
    default_category = "injection"
    default_risk_category = "injection"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)('\s*or\s+'?1'?\s*=\s*'?1)"),
                "critical",
                "Classic SQL tautology",
                "SQL injection tautology pattern (OR 1=1 style): «{matched}».",
                "Use parameterized queries; validate and encode all user input.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bunion(?:\s+all)?\s+select\b"),
                "critical",
                "UNION-based SQL injection",
                "UNION SELECT injection pattern detected: «{matched}».",
                "Blocklist is insufficient—use ORM parameter binding and least-privilege DB roles.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(drop|truncate|alter)\s+table\b"),
                "high",
                "Destructive SQL statement",
                "Destructive DDL/DML phrasing in text: «{matched}».",
                "Restrict DDL permissions; audit queries and enable WAF rules.",
            ),
            PatternSpec(
                re.compile(r"(?i)(--\s*$|;\s*--|'\s*;\s*drop)"),
                "medium",
                "SQL comment terminator",
                "SQL comment or statement chaining pattern: «{matched}».",
                "Treat as untrusted input; sanitize before any SQL composition.",
            ),
        )
