"""
LLM abstraction module for Nutrino.
Provides isolated Ollama client integration, entity extraction schemas, and service layer.
"""

from app.llm.client import OllamaClient
from app.llm.exceptions import (
    LLMException,
    LLMParsingError,
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from app.llm.schemas import (
    ExtractedMealItem,
    MealExtraction,
    MealExtractionRequest,
    MealExtractionResponse,
)
from app.llm.service import LLMService

__all__ = [
    "LLMException",
    "OllamaConnectionError",
    "OllamaTimeoutError",
    "OllamaResponseError",
    "LLMParsingError",
    "OllamaClient",
    "ExtractedMealItem",
    "MealExtraction",
    "MealExtractionRequest",
    "MealExtractionResponse",
    "LLMService",
]
