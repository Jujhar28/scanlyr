class MicrosoftGraphIntegrationError(Exception):
    """Base error for Microsoft Graph integration failures."""


class MicrosoftGraphNotConfiguredError(MicrosoftGraphIntegrationError):
    """Raised when required Microsoft Entra app settings are missing."""


class MicrosoftGraphOAuthError(MicrosoftGraphIntegrationError):
    """Raised when OAuth exchange or state validation fails."""


class MicrosoftGraphApiError(MicrosoftGraphIntegrationError):
    """Raised when Microsoft Graph returns a non-success response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code