"""Detect synthetic / example credentials to avoid false-positive escalations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.scan_security.validation.entropy import is_placeholder_value

_SYNTHETIC_EMAIL_LOCALS = frozenset(
    {
        "test",
        "user",
        "demo",
        "sample",
        "example",
        "foo",
        "bar",
        "admin",
        "jane",
        "john",
        "dummy",
        "fake",
    },
)
_SYNTHETIC_EMAIL_DOMAINS = frozenset(
    {
        "example.com",
        "example.org",
        "example.net",
        "test.com",
        "localhost",
        "invalid",
        "local",
    },
)
_EXPLICIT_TEST_EMAILS = frozenset(
    {
        "test@gmail.com",
        "user@example.com",
        "admin@example.com",
        "test@example.com",
    },
)

_FIXTURE_DISCOURSE = re.compile(
    r"(?i)\b("
    r"test\s+user|test\s+account|for\s+scanlyr|scanlyr\s+account|"
    r"sample\s+account|demo\s+account|example\s+user|"
    r"not\s+a\s+real|fictional|synthetic|dummy\s+data|"
    r"for\s+testing|test\s+case|training\s+example"
    r")\b",
)


@dataclass(frozen=True)
class SyntheticFixtureAssessment:
    is_synthetic: bool
    confidence: float
    reason: str


def is_synthetic_test_email(email: str) -> bool:
    cleaned = email.strip().lower()
    if cleaned in _EXPLICIT_TEST_EMAILS:
        return True
    if "@" not in cleaned:
        return False
    local, _, domain = cleaned.partition("@")
    if domain in _SYNTHETIC_EMAIL_DOMAINS:
        return True
    if local in _SYNTHETIC_EMAIL_LOCALS:
        return True
    if re.match(r"^test\d*$", local):
        return True
    if re.match(r"^(user|demo|sample)\d*$", local):
        return True
    return False


def assess_synthetic_credential_fixture(
    text: str,
    email: str,
    password_value: str,
) -> SyntheticFixtureAssessment:
    """
    True when email + password look like documentation / QA fixtures, not live secrets.
    """
    pwd = password_value.strip().strip("\"'")
    email_syn = is_synthetic_test_email(email)
    pwd_syn = is_placeholder_value(pwd) or _is_common_demo_password(pwd)
    discourse = bool(_FIXTURE_DISCOURSE.search(text))

    if email_syn and pwd_syn:
        return SyntheticFixtureAssessment(
            is_synthetic=True,
            confidence=0.92 if discourse else 0.85,
            reason="example_email_and_placeholder_password",
        )
    if pwd_syn and discourse:
        # Common demo password + explicit test/scan phrasing (e.g. scanlyr account).
        return SyntheticFixtureAssessment(
            is_synthetic=True,
            confidence=0.84,
            reason="placeholder_password_with_test_discourse",
        )
    if email_syn and discourse:
        return SyntheticFixtureAssessment(
            is_synthetic=True,
            confidence=0.78,
            reason="example_email_with_test_discourse",
        )
    return SyntheticFixtureAssessment(is_synthetic=False, confidence=0.0, reason="")


def scan_indicates_synthetic_fixture(
    text: str,
    *,
    findings: tuple[object, ...] | list[object] = (),
) -> bool:
    """True when rules output or text strongly suggests QA / example credentials."""
    from app.scan_security.analysis.context import analyze_text_context

    profile = analyze_text_context(text)
    if profile.is_likely_fixture:
        return True
    for finding in findings:
        evidence = getattr(finding, "evidence", None) or {}
        if isinstance(evidence, dict) and evidence.get("synthetic_fixture"):
            return True
    email_m = re.search(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        text,
    )
    pwd_m = re.search(
        r"(?i)(?:password|passwd|pwd)\s*(?:is|:|=)\s*['\"]?([^\s'\",;]{4,})",
        text,
    )
    if email_m and pwd_m:
        assessment = assess_synthetic_credential_fixture(
            text,
            email_m.group(),
            pwd_m.group(1).strip().strip("\"'"),
        )
        if assessment.is_synthetic and assessment.confidence >= 0.8:
            return True
    return False


def _is_common_demo_password(value: str) -> bool:
    lower = value.lower()
    return lower in {
        "password123",
        "password",
        "pass123",
        "admin123",
        "admin",
        "hunter2",
        "changeme",
        "123456",
        "12345678",
        "qwerty",
        "letmein",
        "welcome1",
    }
