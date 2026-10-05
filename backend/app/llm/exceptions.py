"""
Exceptions for the LLM abstraction and Ollama client integration.
"""


class LLMException(Exception):
    """Base exception for all LLM-related operations."""
    pass


class OllamaConnectionError(LLMException):
    """Raised when the application fails to establish a connection to the Ollama server."""
    pass


class OllamaTimeoutError(LLMException):
    """Raised when an Ollama request times out."""
    pass


class OllamaResponseError(LLMException):
    """Raised when Ollama returns an error status code or invalid response structure."""
    pass


class LLMParsingError(LLMException):
    """Raised when the LLM output cannot be parsed or validated against the expected schema."""
    pass
