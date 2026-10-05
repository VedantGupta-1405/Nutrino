"""
Automated unit and integration tests for the Phase 6 Local LLM layer.
All tests mock the Ollama client/HTTP boundary so the test suite does not require a running Ollama server.
"""

from decimal import Decimal
import json
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.api.v1.endpoints import ai
from app.llm.client import OllamaClient
from app.llm.exceptions import (
    LLMParsingError,
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from app.llm.schemas import ExtractedMealItem, MealExtraction
from app.llm.service import LLMService
from app.schemas.meal import MealType


@pytest.fixture
def mock_ollama_client():
    client = OllamaClient(base_url="http://mock-ollama:11434", model="mock-qwen3:8b", timeout=5.0)
    client.chat = AsyncMock()
    return client


@pytest.fixture
def llm_service(mock_ollama_client):
    return LLMService(client=mock_ollama_client)


# ---------------------------------------------------------------------------
# 1. Service Layer Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_meal_single_item(llm_service, mock_ollama_client):
    """Test 1: Valid structured single item extraction."""
    mock_payload = {
        "meal_type": "BREAKFAST",
        "items": [
            {"food_name": "idli", "quantity": 2, "unit": "piece", "notes": "steamed"}
        ]
    }
    mock_ollama_client.chat.return_value = json.dumps(mock_payload)

    result = await llm_service.extract_meal("I had 2 steamed idlis for breakfast")

    assert isinstance(result, MealExtraction)
    assert result.meal_type == MealType.BREAKFAST
    assert len(result.items) == 1
    assert result.items[0].food_name == "idli"
    assert result.items[0].quantity == Decimal("2")
    assert result.items[0].unit == "piece"
    assert result.items[0].notes == "steamed"


@pytest.mark.asyncio
async def test_extract_meal_multiple_items(llm_service, mock_ollama_client):
    """Test 2: Multiple food items extraction."""
    mock_payload = {
        "meal_type": "LUNCH",
        "items": [
            {"food_name": "chapati", "quantity": 3, "unit": "piece", "notes": None},
            {"food_name": "dal", "quantity": 1, "unit": "bowl", "notes": "tadka"},
            {"food_name": "curd", "quantity": 100, "unit": "gram", "notes": None}
        ]
    }
    mock_ollama_client.chat.return_value = json.dumps(mock_payload)

    result = await llm_service.extract_meal("For lunch I ate 3 chapatis, 1 bowl of dal tadka, and 100g curd")

    assert result.meal_type == MealType.LUNCH
    assert len(result.items) == 3
    assert result.items[0].food_name == "chapati"
    assert result.items[1].food_name == "dal"
    assert result.items[2].unit == "gram"


@pytest.mark.asyncio
async def test_extract_meal_ambiguous_quantity_not_invented(llm_service, mock_ollama_client):
    """Test 3: Ambiguous input preserves null quantity and unit; does NOT invent values."""
    mock_payload = {
        "meal_type": "DINNER",
        "items": [
            {"food_name": "rice", "quantity": None, "unit": None, "notes": None},
            {"food_name": "vegetable curry", "quantity": None, "unit": None, "notes": None}
        ]
    }
    mock_ollama_client.chat.return_value = json.dumps(mock_payload)

    result = await llm_service.extract_meal("I had some rice and vegetable curry for dinner")

    assert result.meal_type == MealType.DINNER
    assert len(result.items) == 2
    assert result.items[0].quantity is None
    assert result.items[0].unit is None
    assert result.items[1].quantity is None
    assert result.items[1].unit is None


@pytest.mark.asyncio
async def test_extract_meal_markdown_wrapped_json(llm_service, mock_ollama_client):
    """Test 4: Handles LLM output wrapped in markdown ```json ... ``` blocks."""
    raw_markdown = """```json
{
  "meal_type": "SNACK",
  "items": [
    {"food_name": "apple", "quantity": 1, "unit": "piece", "notes": null}
  ]
}
```"""
    mock_ollama_client.chat.return_value = raw_markdown

    result = await llm_service.extract_meal("I ate an apple for snack")
    assert result.meal_type == MealType.SNACK
    assert len(result.items) == 1
    assert result.items[0].food_name == "apple"


@pytest.mark.asyncio
async def test_extract_meal_empty_input_rejected(llm_service):
    """Test 5: Empty or whitespace input raises ValueError before calling LLM."""
    with pytest.raises(ValueError, match="Input text cannot be empty"):
        await llm_service.extract_meal("   ")


@pytest.mark.asyncio
async def test_extract_meal_malformed_json_raises_llm_parsing_error(llm_service, mock_ollama_client):
    """Test 6: Malformed non-JSON model output raises LLMParsingError."""
    mock_ollama_client.chat.return_value = "Sorry, I am an AI and cannot help with that."

    with pytest.raises(LLMParsingError, match="Model returned invalid JSON"):
        await llm_service.extract_meal("I had an apple")


@pytest.mark.asyncio
async def test_extract_meal_schema_mismatch_raises_llm_parsing_error(llm_service, mock_ollama_client):
    """Test 7: JSON that violates the Pydantic schema raises LLMParsingError."""
    # items must be a list, passing a string should fail validation
    mock_ollama_client.chat.return_value = json.dumps({"meal_type": "INVALID_TYPE", "items": "not a list"})

    with pytest.raises(LLMParsingError, match="failed schema validation"):
        await llm_service.extract_meal("I had an apple")


@pytest.mark.asyncio
async def test_extract_meal_connection_error_propagated(llm_service, mock_ollama_client):
    """Test 8: OllamaConnectionError is raised when Ollama server is unreachable."""
    mock_ollama_client.chat.side_effect = OllamaConnectionError("Connection refused")

    with pytest.raises(OllamaConnectionError):
        await llm_service.extract_meal("I ate 2 eggs")


@pytest.mark.asyncio
async def test_extract_meal_timeout_propagated(llm_service, mock_ollama_client):
    """Test 9: OllamaTimeoutError is raised when Ollama call times out."""
    mock_ollama_client.chat.side_effect = OllamaTimeoutError("Request timed out")

    with pytest.raises(OllamaTimeoutError):
        await llm_service.extract_meal("I ate 2 eggs")


# ---------------------------------------------------------------------------
# 2. HTTP Endpoint Tests (/api/v1/ai/extract-meal)
# ---------------------------------------------------------------------------

def test_api_extract_meal_success(client: TestClient):
    """Test 10: Successful HTTP request to /api/v1/ai/extract-meal."""
    mock_extraction = MealExtraction(
        meal_type=MealType.BREAKFAST,
        items=[
            ExtractedMealItem(food_name="idli", quantity=Decimal("2"), unit="piece", notes=None),
            ExtractedMealItem(food_name="sambar", quantity=Decimal("1"), unit="bowl", notes=None),
        ]
    )

    with patch("app.api.v1.endpoints.ai.get_llm_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_svc.extract_meal.return_value = mock_extraction
        mock_svc.model_name = "qwen3:8b"
        mock_get_svc.return_value = mock_svc

        response = client.post(
            "/api/v1/ai/extract-meal",
            json={"text": "I had 2 idlis and a bowl of sambar for breakfast."}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model"] == "qwen3:8b"
        assert data["extraction"]["meal_type"] == "BREAKFAST"
        assert len(data["extraction"]["items"]) == 2
        assert data["extraction"]["items"][0]["food_name"] == "idli"
        assert float(data["extraction"]["items"][0]["quantity"]) == 2.0


def test_api_extract_meal_empty_text_validation_error(client: TestClient):
    """Test 11: Empty text fails request validation."""
    response = client.post(
        "/api/v1/ai/extract-meal",
        json={"text": ""}
    )
    assert response.status_code == 422


def test_api_extract_meal_ollama_unavailable_returns_503(client: TestClient):
    """Test 12: Ollama connection failure returns HTTP 503."""
    with patch("app.api.v1.endpoints.ai.get_llm_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_svc.extract_meal.side_effect = OllamaConnectionError("Server unreachable")
        mock_get_svc.return_value = mock_svc

        response = client.post(
            "/api/v1/ai/extract-meal",
            json={"text": "I ate 2 eggs"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "unavailable" in data["detail"].lower()


def test_api_extract_meal_timeout_returns_504(client: TestClient):
    """Test 13: Ollama timeout returns HTTP 504."""
    with patch("app.api.v1.endpoints.ai.get_llm_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_svc.extract_meal.side_effect = OllamaTimeoutError("Timed out")
        mock_get_svc.return_value = mock_svc

        response = client.post(
            "/api/v1/ai/extract-meal",
            json={"text": "I ate 2 eggs"}
        )

        assert response.status_code == 504
        data = response.json()
        assert "timed out" in data["detail"].lower()


def test_api_extract_meal_parsing_error_returns_502(client: TestClient):
    """Test 14: Model parsing/schema error returns HTTP 502."""
    with patch("app.api.v1.endpoints.ai.get_llm_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_svc.extract_meal.side_effect = LLMParsingError("Invalid schema")
        mock_get_svc.return_value = mock_svc

        response = client.post(
            "/api/v1/ai/extract-meal",
            json={"text": "I ate 2 eggs"}
        )

        assert response.status_code == 502
        data = response.json()
        assert "failed to extract" in data["detail"].lower()
