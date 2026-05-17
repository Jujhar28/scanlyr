"""AI re-verification of rule-engine findings (hybrid mode)."""

from __future__ import annotations

import logging

from app.ai_providers.errors import (
    AIProviderConfigError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.ai_providers.fallback import FallbackAIProvider
from app.ai_providers.factory import get_ai_provider
from app.ai_providers.gemini import GeminiProvider
from app.ai_providers.groq import GroqProvider
from app.ai_providers.schemas import HybridReverifyOutcome, ProviderAnalysisOutcome
from app.scan_security.analysis.context import analyze_text_context
from app.scan_security.context import ContentKind
from app.scan_security.schemas.findings import SecurityFinding, Severity
from app.scan_security.schemas.results import ScanAnalysisResult
from app.scan_security.services.scoring import aggregate_findings
from app.core.config import Settings, get_settings
from app.services.scan_ai_layer_service import ai_keys_configured

logger = logging.getLogger(__name__)

_SEVERITY_ORDER: tuple[Severity, ...] = ("low", "medium", "high", "critical")


def _findings_for_prompt(findings: tuple[SecurityFinding, ...]) -> list[dict[str, object]]:
    return [
        {
            "index": i,
            "title": f.title,
            "severity": f.severity,
            "description": f.description,
            "detector_id": f.detector_id,
        }
        for i, f in enumerate(findings)
    ]


def _invoke_hybrid_reverify(
    provider: object,
    input_text: str,
    findings: list[dict[str, object]],
) -> HybridReverifyOutcome:
    if isinstance(provider, FallbackAIProvider):
        return provider.analyze_hybrid_reverify_with_outcome(input_text, findings)
    if isinstance(provider, GeminiProvider):
        result = provider.analyze_hybrid_reverify(input_text, findings)
        return HybridReverifyOutcome(
            result=result,
            provider_id="gemini",
            fallback_used=False,
            attempted_providers=["gemini"],
        )
    if isinstance(provider, GroqProvider):
        result = provider.analyze_hybrid_reverify(input_text, findings)
        return HybridReverifyOutcome(
            result=result,
            provider_id="groq",
            fallback_used=False,
            attempted_providers=["groq"],
        )
    raise AIProviderConfigError("Provider does not support hybrid re-verify.")


def try_ai_hybrid_reverify_rules(
    input_text: str,
    rules: ScanAnalysisResult,
    *,
    content_type: ContentKind = "auto",
    settings: Settings | None = None,
) -> tuple[ScanAnalysisResult, ProviderAnalysisOutcome | None]:
    """
    Re-verify rule findings with AI, then return adjusted rules + AI outcome for fusion.

    Returns ``(rules, None)`` when re-verify is skipped or fails (caller may fall back).
    """
    cfg = settings or get_settings()
    if not cfg.scan_ai_fusion_enabled or not ai_keys_configured(cfg):
        return rules, None
    if not rules.findings:
        return rules, None

    findings_payload = _findings_for_prompt(rules.findings)
    timeout = cfg.scan_ai_provider_timeout_seconds
    retries = cfg.scan_ai_max_retries

    try:
        provider = get_ai_provider(settings=cfg, timeout_seconds=timeout, max_retries=retries)
        outcome = _invoke_hybrid_reverify(provider, input_text, findings_payload)
        adjusted = apply_hybrid_reverify_to_rules(
            rules,
            outcome.result,
            input_text=input_text,
            content_type=content_type,
        )
        logger.info(
            "scan_ai_reverify_succeeded",
            extra={
                "ai_provider": outcome.provider_id,
                "findings_in": len(rules.findings),
                "findings_out": len(adjusted.findings),
                "ai_score": outcome.result.risk_score,
                "rules_score_after": adjusted.risk_score,
            },
        )
        return adjusted, outcome.as_provider_analysis_outcome()
    except AIProviderTimeoutError as exc:
        logger.warning("scan_ai_reverify_timeout", extra={"error": str(exc)})
        return rules, None
    except (AIProviderError, AIProviderConfigError, AIProviderResponseError) as exc:
        logger.warning(
            "scan_ai_reverify_failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return rules, None
    except Exception as exc:
        logger.exception(
            "scan_ai_reverify_unexpected",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return rules, None


def apply_hybrid_reverify_to_rules(
    rules: ScanAnalysisResult,
    reverify: object,
    *,
    input_text: str,
    content_type: ContentKind = "auto",
) -> ScanAnalysisResult:
    """Apply per-finding AI verdicts and recompute rules aggregate score."""
    from app.ai_providers.schemas import HybridReverifyResult

    if not isinstance(reverify, HybridReverifyResult):
        raise TypeError("reverify must be HybridReverifyResult")

    verdict_by_index = {v.index: v for v in reverify.finding_verdicts}
    kept: list[SecurityFinding] = []

    for i, finding in enumerate(rules.findings):
        verdict = verdict_by_index.get(i)
        if verdict is None:
            kept.append(finding)
            continue
        evidence = dict(finding.evidence)
        evidence["ai_verdict"] = verdict.verdict
        evidence["ai_reason"] = verdict.reason

        if verdict.verdict == "dismiss":
            continue
        if verdict.verdict == "downgrade":
            sev = verdict.adjusted_severity or _lower_severity(finding.severity)
            kept.append(
                finding.model_copy(
                    update={
                        "severity": sev,
                        "confidence": round(finding.confidence * 0.5, 3),
                        "evidence": evidence,
                    },
                ),
            )
            continue
        kept.append(finding.model_copy(update={"evidence": evidence}))

    profile = analyze_text_context(input_text)

    return aggregate_findings(
        kept,
        content_kind=content_type,
        context_profile=profile,
    )


def _lower_severity(current: Severity) -> Severity:
    idx = _SEVERITY_ORDER.index(current)
    return _SEVERITY_ORDER[max(0, idx - 1)]
