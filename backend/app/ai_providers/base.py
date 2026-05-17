"""Abstract interface for interchangeable external AI text analysis providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.ai_providers.schemas import TextAnalysisResult


class AIProvider(ABC):
    """
    Adapter for a single vendor LLM API.

    Implementations perform HTTP/RPC only: prompt assembly, API call, JSON parse/validate.
    No scan persistence, rule engine, or tenant logic belongs here.
    """

    provider_id: ClassVar[str]

    @abstractmethod
    def analyze_text(self, input_text: str) -> TextAnalysisResult:
        """
        Send ``input_text`` to the vendor model and return validated structured analysis.

        Raises:
            AIProviderConfigError: API key or model configuration missing.
            AIProviderResponseError: Network failure or invalid model output.
        """

    def analyze_text_as_dict(self, input_text: str) -> dict[str, object]:
        """Convenience wrapper returning JSON-serializable dict."""
        return self.analyze_text(input_text).as_dict()
