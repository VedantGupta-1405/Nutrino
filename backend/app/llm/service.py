"""
LLM Service layer for natural language understanding and structured extraction.
Strictly isolated: does NOT touch SQLAlchemy, database models, food catalogs, or nutrition calculations.
"""

import json
import logging
import re
import time
from typing import Optional
from pydantic import ValidationError
from app.llm.client import OllamaClient
from app.llm.exceptions import LLMParsingError
from app.llm.prompts import build_meal_extraction_messages
from app.llm.schemas import MealExtraction

logger = logging.getLogger(__name__)


class LLMService:
    """
    High-level service for coordinating LLM inference and structured entity extraction.
    """

    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()

    @property
    def model_name(self) -> str:
        """Returns the configured model identifier."""
        return self.client.model

    async def extract_meal(self, text: str) -> MealExtraction:
        """
        Parses a natural-language meal description into a validated structured MealExtraction schema.

        :param text: User's unstructured food description.
        :return: Validated MealExtraction instance.
        :raises ValueError: If input text is empty or whitespace.
        :raises OllamaConnectionError: If Ollama cannot be reached.
        :raises OllamaTimeoutError: If Ollama times out.
        :raises LLMParsingError: If model response is invalid JSON or does not conform to MealExtraction schema.
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Input text cannot be empty.")

        messages = build_meal_extraction_messages(cleaned_text)

        logger.info(
            "LLM meal extraction started (model: %s, input_len: %d chars)",
            self.client.model,
            len(cleaned_text),
        )
        start_time = time.perf_counter()

        raw_output = await self.client.chat(messages=messages, format="json", temperature=0.0)

        duration = time.perf_counter() - start_time

        # Clean potential markdown wrapping if returned by the model
        json_content = raw_output.strip()
        if json_content.startswith("```"):
            json_content = re.sub(r"^```(?:json)?\s*", "", json_content, flags=re.MULTILINE)
            json_content = re.sub(r"\s*```$", "", json_content, flags=re.MULTILINE)
            json_content = json_content.strip()

        try:
            parsed_data = json.loads(json_content)
        except json.JSONDecodeError as exc:
            logger.error("LLM output is not valid JSON (duration: %.2fs): %s", duration, exc)
            raise LLMParsingError(f"Model returned invalid JSON: {exc}") from exc

        try:
            extraction = MealExtraction.model_validate(parsed_data)
        except ValidationError as exc:
            logger.error("LLM output failed Pydantic validation (duration: %.2fs): %s", duration, exc)
            raise LLMParsingError(f"Model output failed schema validation: {exc}") from exc

        logger.info(
            "LLM meal extraction completed successfully in %.2fs (items: %d, meal_type: %s)",
            duration,
            len(extraction.items),
            extraction.meal_type.value if extraction.meal_type else "None",
        )
        return extraction
