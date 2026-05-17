from __future__ import annotations

from app.scan_security.context import ContentKind
from app.scan_security.detectors.api_key_leak import ApiKeyLeakDetector
from app.scan_security.detectors.base import SecurityDetector
from app.scan_security.detectors.credential_bundle import CredentialBundleDetector
from app.scan_security.detectors.command_injection import CommandInjectionDetector
from app.scan_security.detectors.hardcoded_credentials import HardcodedCredentialsDetector
from app.scan_security.detectors.jwt_exposure import JwtExposureDetector
from app.scan_security.detectors.phishing import PhishingIndicatorDetector
from app.scan_security.detectors.prompt_injection import PromptInjectionDetector
from app.scan_security.detectors.private_key_pem import PrivateKeyPemDetector
from app.scan_security.detectors.secrets_tokens import SecretsTokensDetector
from app.scan_security.detectors.shell_commands import SuspiciousShellCommandDetector
from app.scan_security.detectors.sql_injection import SqlInjectionDetector
from app.scan_security.detectors.suspicious_urls import SuspiciousUrlDetector
from app.scan_security.detectors.unsafe_python import UnsafePythonDetector
from app.scan_security.llm.registry import llm_output_detectors, llm_prompt_detectors


def core_security_detectors() -> tuple[SecurityDetector, ...]:
    """General application-security detectors (prompt, output, or auto)."""
    return (
        ApiKeyLeakDetector(),
        SecretsTokensDetector(),
        CredentialBundleDetector(),
        PrivateKeyPemDetector(),
        JwtExposureDetector(),
        HardcodedCredentialsDetector(),
        SqlInjectionDetector(),
        CommandInjectionDetector(),
        SuspiciousShellCommandDetector(),
        PromptInjectionDetector(),
        PhishingIndicatorDetector(),
        SuspiciousUrlDetector(),
        UnsafePythonDetector(),
    )


def default_security_detectors() -> tuple[SecurityDetector, ...]:
    """Full detector set for ``content_type=auto`` (backward compatible)."""
    return _dedupe_detectors(
        (*core_security_detectors(), *llm_prompt_detectors(), *llm_output_detectors()),
    )


def detectors_for_content_type(content_type: ContentKind) -> tuple[SecurityDetector, ...]:
    """Select detectors for prompt-only, output-only, or full scans."""
    if content_type == "prompt":
        return _dedupe_detectors((*core_security_detectors(), *llm_prompt_detectors()))
    if content_type == "output":
        return _dedupe_detectors((*core_security_detectors(), *llm_output_detectors()))
    return default_security_detectors()


def _dedupe_detectors(detectors: tuple[SecurityDetector, ...]) -> tuple[SecurityDetector, ...]:
    seen: set[str] = set()
    out: list[SecurityDetector] = []
    for d in detectors:
        if d.detector_id in seen:
            continue
        seen.add(d.detector_id)
        out.append(d)
    return tuple(out)


__all__ = [
    "core_security_detectors",
    "default_security_detectors",
    "detectors_for_content_type",
]
