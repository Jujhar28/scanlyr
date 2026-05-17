"""Detect combined credential leaks (email + password in the same text)."""

from __future__ import annotations

import re

from app.scan_security.analysis.context import analyze_text_context
from app.scan_security.analysis.fixtures import assess_synthetic_credential_fixture
from app.scan_security.detectors.base import SecurityDetector
from app.scan_security.schemas.findings import SecurityFinding

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PASSWORD_ASSIGN_RE = re.compile(
    r"(?i)(?:password|passwd|pwd)\s*(?:is|:|=)\s*['\"]?([^\s'\",;]{4,})",
)
_PASSWORD_LITERAL_RE = re.compile(
    r"(?i)password\s*[:=]\s*['\"]([^'\"]{4,})['\"]",
)


class CredentialBundleDetector(SecurityDetector):
    """
    Escalates when identifiable account material appears with a password value.

    Context-aware: example/test pairs (test@gmail.com + password123) are informational only.
    """

    detector_id = "credential_bundle"
    default_finding_type = "secret_password"

    def detect_with_context(self, context) -> list[SecurityFinding]:
        text = context.text
        email_match = _EMAIL_RE.search(text)
        pwd_match = _PASSWORD_ASSIGN_RE.search(text) or _PASSWORD_LITERAL_RE.search(text)
        if not email_match or not pwd_match:
            return []

        email = email_match.group()
        pwd_value = pwd_match.group(1).strip().strip("\"'")
        profile = analyze_text_context(text)
        fixture = assess_synthetic_credential_fixture(text, email, pwd_value)

        if fixture.is_synthetic:
            severity = "low"
            confidence = round(0.42 * fixture.confidence, 3)
            description = (
                f"Example-style credentials detected ({email} with a common placeholder password). "
                "This resembles test or documentation data, not a confirmed live account leak."
            )
            remediation = (
                "If this is real production data, rotate credentials and remove from logs. "
                "Otherwise no immediate action — avoid pasting even test passwords into production AI tools."
            )
        elif _is_trivial_password(pwd_value):
            severity = "medium"
            confidence = 0.72
            description = (
                f"Email ({email}) appears with a weak or common password value. "
                "Verify whether this is an active account credential."
            )
            remediation = (
                "Rotate the password if this is a real account, and use a secrets manager "
                "instead of plain-text sharing."
            )
        else:
            severity = "high"
            confidence = 0.91
            description = (
                f"Email ({email}) and password value appear together — "
                "likely a live account credential in plain text."
            )
            remediation = (
                "Rotate the password immediately, remove this content from AI logs, "
                "and use secure credential sharing (vault link, not plain text)."
            )

        if profile.is_likely_fixture and fixture.is_synthetic:
            confidence = round(confidence * 0.85, 3)

        return [
            SecurityFinding(
                type="secret_password",
                detector_id=self.detector_id,
                category="credential_exposure",
                risk_category="credential_exposure",
                severity=severity,
                title="Account credentials disclosed"
                if not fixture.is_synthetic
                else "Example credentials referenced",
                description=description,
                remediation=remediation,
                confidence=confidence,
                evidence={
                    "email": email,
                    "password_value_redacted": _redact(pwd_value),
                    "synthetic_fixture": fixture.is_synthetic,
                    "fixture_reason": fixture.reason or None,
                    "start": min(email_match.start(), pwd_match.start()),
                    "end": max(email_match.end(), pwd_match.end()),
                },
            ),
        ]


def _is_trivial_password(value: str) -> bool:
    lower = value.lower()
    if lower in {"password", "pass", "secret", "test", "demo", "123456", "12345678"}:
        return True
    return lower in ("password123", "changeme", "hunter2", "admin", "admin123")


def _redact(value: str) -> str:
    if len(value) <= 2:
        return "***"
    return value[0] + "***" + value[-1]
