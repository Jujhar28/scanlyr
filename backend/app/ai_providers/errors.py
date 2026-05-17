"""Exceptions raised by external AI provider adapters."""


class AIProviderError(Exception):
    """Base error for provider transport, configuration, or response parsing."""


class AIProviderConfigError(AIProviderError):
    """Missing or invalid provider configuration (e.g. API key)."""


class AIProviderResponseError(AIProviderError):
    """Provider returned an unexpected or unparseable payload."""


class AIProviderTimeoutError(AIProviderResponseError):
    """Provider request exceeded the configured timeout."""
