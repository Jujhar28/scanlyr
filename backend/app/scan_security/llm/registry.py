from __future__ import annotations

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import SecurityDetector
from app.scan_security.llm.data_exfiltration import DataExfiltrationDetector
from app.scan_security.llm.jailbreak import JailbreakDetector
from app.scan_security.llm.output_moderation import OutputModerationDetector
from app.scan_security.llm.provider_risk import CompositeProviderRiskDetector
from app.scan_security.llm.sensitive_data import SensitiveDataExposureDetector
from app.scan_security.llm.system_prompt_leak import SystemPromptLeakageDetector
from app.scan_security.llm.unsafe_agent import UnsafeAgentActionDetector
from app.scan_security.llm.unsafe_instructions import UnsafeInstructionsDetector


def llm_prompt_detectors() -> tuple[SecurityDetector, ...]:
    """Detectors for user prompts and agent inputs."""
    return (
        JailbreakDetector(),
        SystemPromptLeakageDetector(),
        DataExfiltrationDetector(),
        SensitiveDataExposureDetector(),
        UnsafeAgentActionDetector(),
        UnsafeInstructionsDetector(),
        CompositeProviderRiskDetector(),
    )


def llm_output_detectors() -> tuple[SecurityDetector, ...]:
    """Detectors for model completions and tool outputs."""
    return (
        SensitiveDataExposureDetector(),
        OutputModerationDetector(),
    )


def detectors_for_content_kind(kind: ContentKind) -> frozenset[ContentKind]:
    if kind == "prompt":
        return frozenset({"auto", "prompt"})
    if kind == "output":
        return frozenset({"auto", "output"})
    return frozenset({"auto", "prompt", "output"})
