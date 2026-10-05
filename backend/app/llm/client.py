"""
Dedicated async client for communicating with the local Ollama server.
Responsible solely for transport, timeouts, connection handling, and raw response extraction.
"""

import logging
from typing import Any, Dict, List, Optional, Union
import httpx
from app.config.settings import settings
from app.llm.exceptions import (
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama REST API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def is_available(self) -> bool:
        """
        Quick liveness probe to verify if Ollama server is reachable without blocking startup.
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def chat(
        self,
        messages: List[Dict[str, str]],
        format: Optional[Union[str, Dict[str, Any]]] = "json",
        temperature: float = 0.0,
    ) -> str:
        """
        Sends a non-streaming chat request to Ollama.

        :param messages: List of message dictionaries with 'role' and 'content' keys.
        :param format: Output format (e.g. 'json' for JSON enforcement).
        :param temperature: Generation temperature (default 0.0 for deterministic extraction).
        :return: Assistant's response content string.
        """
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
            },
        }
        if format:
            payload["format"] = format

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("Failed to connect to Ollama at %s: %s", self.base_url, exc)
            raise OllamaConnectionError(
                f"Could not connect to Ollama server at {self.base_url}. Please ensure Ollama is running."
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out after %.1f seconds: %s", self.timeout, exc)
            raise OllamaTimeoutError(
                f"Ollama request timed out after {self.timeout} seconds."
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Ollama HTTP request error: %s", exc)
            raise OllamaConnectionError(f"HTTP communication with Ollama failed: {exc}") from exc

        if response.status_code != 200:
            logger.error(
                "Ollama returned error HTTP status %d: %s",
                response.status_code,
                response.text,
            )
            raise OllamaResponseError(
                f"Ollama returned error status {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            content = data["message"]["content"]
            return content
        except (KeyError, ValueError) as exc:
            logger.error("Invalid response format received from Ollama: %s", response.text)
            raise OllamaResponseError(f"Malformed response structure from Ollama: {exc}") from exc
