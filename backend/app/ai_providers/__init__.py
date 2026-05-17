"""
External LLM provider adapters for optional AI-assisted text analysis.

Default resolution (``AI_PROVIDER=auto``): Gemini primary, Groq fallback.
"""

from app.ai_providers.base import AIProvider
from app.ai_providers.errors import AIProviderConfigError, AIProviderError, AIProviderResponseError
from app.ai_providers.factory import get_ai_provider, registered_provider_ids
from app.ai_providers.fallback import FallbackAIProvider
from app.ai_providers.gemini import GeminiProvider
from app.ai_providers.groq import GroqProvider
from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult

__all__ = [
    "AIProvider",
    "AIProviderConfigError",
    "AIProviderError",
    "AIProviderResponseError",
    "FallbackAIProvider",
    "GeminiProvider",
    "GroqProvider",
    "ProviderAnalysisOutcome",
    "TextAnalysisResult",
    "get_ai_provider",
    "registered_provider_ids",
]
