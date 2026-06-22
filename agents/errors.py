"""Pipeline error types for user-facing messages."""


class BureaucracyAgentError(Exception):
    """Base error for the letter analysis pipeline."""


class MissingApiKeyError(BureaucracyAgentError):
    """Raised when GOOGLE_API_KEY is not configured."""


class EmptyInputError(BureaucracyAgentError):
    """Raised when letter text is empty."""


class GeminiApiError(BureaucracyAgentError):
    """Raised when the Gemini API call fails."""


class QuotaExceededError(GeminiApiError):
    """Raised when Gemini returns 429 / RESOURCE_EXHAUSTED."""


class PipelineError(BureaucracyAgentError):
    """Raised for unexpected pipeline failures."""
