"""Post-detection refinement: validation, severity calibration, suppression."""

from __future__ import annotations

import re
from typing import Literal

from app.scan_security.analysis.context import TextContextProfile, analyze_text_context
from app.scan_security.analysis.fixtures import assess_synthetic_credential_fixture, is_synthetic_test_email
from app.scan_security.schemas.findings import SecurityFinding, Severity
from app.scan_security.validation.pci import luhn_check, normalize_card_digits
from app.scan_security.validation.secrets import SecretStrength, classify_secret_match

ScanStrictness = Literal["permissive", "balanced", "strict"]

_SEVERITY_ORDER: tuple[Severity, ...] = ("low", "medium", "high", "critical")
_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


def refine_findings(
    findings: list[SecurityFinding],
    text: str,
    *,
    strictness: ScanStrictness = "balanced",
) -> list[SecurityFinding]:
    profile = analyze_text_context(text)
    refined: list[SecurityFinding] = []
    for finding in findings:
        updated = _refine_one(finding, text, profile, strictness)
        if updated is not None:
            refined.append(updated)
    return _dedupe_overlapping(refined)


def _refine_one(
    finding: SecurityFinding,
    text: str,
    profile: TextContextProfile,
    strictness: ScanStrictness,
) -> SecurityFinding | None:
    evidence = dict(finding.evidence)
    matched = _extract_matched_snippet(text, evidence)

    if finding.detector_id == "credential_bundle":
        return _refine_credential_bundle(finding, text, profile, strictness)

    if finding.type == "sensitive_data" and finding.title == "Email address":
        email = matched or ""
        if email:
            pwd_value = _extract_password_from_text(text)
            fixture = (
                assess_synthetic_credential_fixture(text, email, pwd_value)
                if pwd_value
                else None
            )
            if fixture and fixture.is_synthetic:
                if strictness == "permissive" or (
                    strictness == "balanced" and profile.is_likely_fixture
                ):
                    return None
                return _downgrade(
                    finding,
                    severity="low",
                    confidence=round(finding.confidence * 0.35, 3),
                    evidence={**evidence, "synthetic_fixture": True},
                    note="email_in_fixture_context",
                )
        if email and is_synthetic_test_email(email):
            if strictness == "permissive" or (strictness == "balanced" and profile.is_likely_fixture):
                return None
            return _downgrade(
                finding,
                severity="low",
                confidence=round(finding.confidence * 0.4, 3),
                evidence={**evidence, "synthetic_email": True},
                note="example_email_address",
            )

    if finding.type in ("secret_password", "api_key_leak", "hardcoded_credential", "jwt_token"):
        classification = classify_secret_match(matched or finding.title, finding_type=str(finding.type))
        evidence["secret_strength"] = classification.strength.value
        if classification.kind:
            evidence["secret_kind"] = classification.kind

        if classification.strength == SecretStrength.benign:
            if strictness == "permissive":
                return None
            return _downgrade(
                finding,
                severity="low",
                confidence=round(finding.confidence * 0.35, 3),
                evidence=evidence,
                note="placeholder_or_benign",
            )

        if classification.strength in (SecretStrength.weak, SecretStrength.likely) and (
            profile.is_mostly_benign or profile.is_likely_fixture
        ):
            if strictness != "strict":
                return None
            return _downgrade(
                finding,
                severity="low",
                confidence=round(finding.confidence * 0.5, 3),
                evidence=evidence,
                note="weak_signal_benign_context",
            )

        confidence = round(
            min(0.99, finding.confidence * classification.confidence_multiplier),
            3,
        )
        severity = finding.severity
        if classification.strength == SecretStrength.confirmed:
            severity = _bump_severity(severity, 1 if strictness == "strict" else 0)
        elif classification.strength == SecretStrength.weak:
            severity = _bump_severity(severity, -1)

        return finding.model_copy(update={"confidence": confidence, "severity": severity, "evidence": evidence})

    if finding.type == "sensitive_data" and "Payment card" in finding.title:
        card = _CARD_PATTERN.search(text)
        if card and not luhn_check(normalize_card_digits(card.group())):
            if strictness == "permissive":
                return None
            return _downgrade(
                finding,
                severity="low",
                confidence=round(finding.confidence * 0.4, 3),
                evidence={**evidence, "luhn_valid": False},
                note="invalid_card_checksum",
            )
        evidence["luhn_valid"] = True
        return finding.model_copy(update={"evidence": evidence, "confidence": min(0.99, finding.confidence + 0.08)})

    if finding.type in ("prompt_injection", "jailbreak") and strictness == "strict":
        return finding.model_copy(
            update={
                "severity": _bump_severity(finding.severity, 1),
                "confidence": min(0.99, finding.confidence + 0.05),
            },
        )

    if strictness == "permissive" and finding.severity == "low" and finding.confidence < 0.62:
        return None

    return finding


def _refine_credential_bundle(
    finding: SecurityFinding,
    text: str,
    profile: TextContextProfile,
    strictness: ScanStrictness,
) -> SecurityFinding | None:
    evidence = dict(finding.evidence)
    email = str(evidence.get("email") or "")
    if evidence.get("synthetic_fixture"):
        if strictness == "permissive":
            return None
        if strictness == "balanced" and profile.is_likely_fixture:
            return None
        return finding

    pwd_value = _extract_password_from_text(text)
    fixture = assess_synthetic_credential_fixture(text, email, pwd_value)
    if fixture.is_synthetic:
        evidence["synthetic_fixture"] = True
        evidence["fixture_reason"] = fixture.reason
        if strictness == "permissive":
            return None
        if strictness == "balanced" and profile.is_mostly_benign:
            return None
        return _downgrade(
            finding,
            severity="low",
            confidence=round(finding.confidence * 0.45, 3),
            evidence=evidence,
            note="synthetic_credential_fixture",
        )
    return finding


def _extract_password_from_text(text: str) -> str:
    m = re.search(
        r"(?i)(?:password|passwd|pwd)\s*(?:is|:|=)\s*['\"]?([^\s'\",;]{4,})",
        text,
    )
    if not m:
        m = re.search(r"(?i)password\s*[:=]\s*['\"]([^'\"]{4,})['\"]", text)
    return m.group(1).strip().strip("\"'") if m else ""


def _extract_matched_snippet(text: str, evidence: dict) -> str:
    start = evidence.get("start")
    end = evidence.get("end")
    if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
        return text[start:end]
    return ""


def _downgrade(
    finding: SecurityFinding,
    *,
    severity: Severity,
    confidence: float,
    evidence: dict,
    note: str,
) -> SecurityFinding:
    evidence["refinement"] = note
    return finding.model_copy(update={"severity": severity, "confidence": confidence, "evidence": evidence})


def _bump_severity(current: Severity, steps: int) -> Severity:
    idx = _SEVERITY_ORDER.index(current)
    return _SEVERITY_ORDER[min(len(_SEVERITY_ORDER) - 1, max(0, idx + steps))]


def _dedupe_overlapping(findings: list[SecurityFinding]) -> list[SecurityFinding]:
    """Drop duplicate hits on the same span (keep highest severity)."""
    by_span: dict[tuple[int, int], SecurityFinding] = {}
    for f in findings:
        start = f.evidence.get("start")
        end = f.evidence.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            snippet = str(f.evidence.get("snippet") or f.title)
            line_no = f.evidence.get("line_number")
            key = (
                -1,
                hash((f.detector_id, snippet, line_no, f.type, f.description)),
            )
        else:
            key = (start, end)
        existing = by_span.get(key)
        if existing is None or _SEVERITY_ORDER.index(f.severity) > _SEVERITY_ORDER.index(
            existing.severity,
        ):
            by_span[key] = f
    return list(by_span.values())
