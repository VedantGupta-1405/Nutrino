"""
Development endpoints for AI / LLM layer verification.
These endpoints are isolated test harnesses for natural-language entity extraction
and do NOT interact with the database, meals table, or user profiles.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.llm.exceptions import (
    LLMParsingError,
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from app.llm.schemas import MealExtractionRequest, MealExtractionResponse
from app.llm.service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])

# Shared service instance for dependency injection
_llm_service = LLMService()


def get_llm_service() -> LLMService:
    return _llm_service


@router.post(
    "/extract-meal",
    response_model=MealExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured meal items from natural language (Development/Verification endpoint)",
    description=(
        "Analyzes a natural language meal description using the local LLM (Qwen 3 8B / Ollama) "
        "and returns structured, validated food items with quantities and units. "
        "This endpoint does NOT perform database mutations or calculate nutrition values."
    ),
)
async def extract_meal(payload: MealExtractionRequest) -> MealExtractionResponse:
    """
    Extracts structured meal entities from user's natural language input.
    """
    service = get_llm_service()

    try:
        extraction = await service.extract_meal(payload.text)
        return MealExtractionResponse(
            success=True,
            extraction=extraction,
            model=service.model_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except OllamaConnectionError as exc:
        logger.error("AI service connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please verify that the local Ollama server is running.",
        )
    except OllamaTimeoutError as exc:
        logger.error("AI service timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timed out while processing the extraction request.",
        )
    except (OllamaResponseError, LLMParsingError) as exc:
        logger.error("AI service parsing error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to extract structured data from model response: {exc}",
        )
