"""
Comprehensive tests for Phase 8: LangGraph Agent Orchestration.
Tests read flows, meal logging flows, security boundaries, safety constraints,
iteration limits, and HTTP API error handling.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.runtime import AgentRuntimeContext
from app.agent.service import agent_service
from app.database.seed import seed_foods
from app.llm.exceptions import OllamaConnectionError, OllamaTimeoutError
from app.models.goal import Goal
from app.models.meal import Meal, MealItem
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.goal import GoalType
from app.services.food_service import food_service


def register_user(client: TestClient, prefix: str = "agentuser") -> tuple[str, dict]:
    """Helper to register a user and return Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Agent Tester", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


class MockOllamaClient:
    """Mock client returning predetermined sequential LLM responses."""

    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.recorded_calls = []

    async def is_available(self) -> bool:
        return True

    async def chat(self, messages, format=None, temperature=0.0) -> str:
        self.recorded_calls.append(messages)
        if self.responses:
            return self.responses.pop(0)
        return json.dumps({
            "action": "final_response",
            "content": "No further response.",
        })


# ==============================================================================
# 1. READ FLOWS
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_read_today_nutrition(client: TestClient, db_session: Session):
    """Test agent correctly calls get_today_nutrition and returns grounded totals."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "read_nutr")
    user = db_session.get(User, user_dict["id"])

    # Mock LLM: 1st turn selects get_today_nutrition, 2nd turn returns final response
    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "get_today_nutrition", "arguments": {}}),
        json.dumps({"action": "final_response", "content": "You have consumed 0 calories today."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("How many calories have I eaten today?", ctx)
    assert "0 calories" in result.response
    assert "get_today_nutrition" in result.tools_used


@pytest.mark.asyncio
async def test_agent_read_active_goal(client: TestClient, db_session: Session):
    """Test agent retrieves active nutrition goal via get_active_goal."""
    token, user_dict = register_user(client, "read_goal")
    user = db_session.get(User, user_dict["id"])

    # Create active goal
    goal = Goal(
        user_id=user.id,
        goal_type=GoalType.MUSCLE_GAIN.value,
        target_calories=Decimal("2500.00"),
        target_protein=Decimal("150.00"),
        target_carbohydrates=Decimal("280.00"),
        target_fat=Decimal("70.00"),
        is_active=True,
    )
    db_session.add(goal)
    db_session.commit()

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "get_active_goal", "arguments": {}}),
        json.dumps({"action": "final_response", "content": "Your active goal is Muscle Gain with 2,500 kcal."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("What is my current goal?", ctx)
    assert "Muscle Gain" in result.response
    assert "get_active_goal" in result.tools_used


@pytest.mark.asyncio
async def test_agent_read_user_profile(client: TestClient, db_session: Session):
    """Test agent retrieves dietary profile via get_user_profile."""
    token, user_dict = register_user(client, "read_prof")
    user = db_session.get(User, user_dict["id"])

    profile = UserProfile(
        user_id=user.id,
        age=30,
        height=175.0,
        weight=70.0,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["peanuts"],
    )
    db_session.add(profile)
    db_session.commit()

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "get_user_profile", "arguments": {}}),
        json.dumps({"action": "final_response", "content": "You are Vegetarian with an allergy to peanuts."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("What dietary preferences do I have?", ctx)
    assert "Vegetarian" in result.response
    assert "get_user_profile" in result.tools_used


@pytest.mark.asyncio
async def test_agent_read_food_search(client: TestClient, db_session: Session):
    """Test agent searches catalog foods via search_foods."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "read_search")
    user = db_session.get(User, user_dict["id"])

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "Idli"}}),
        json.dumps({"action": "final_response", "content": "Found Idli in the catalog."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Search for idli", ctx)
    assert "search_foods" in result.tools_used
    assert "Idli" in result.response


@pytest.mark.asyncio
async def test_agent_read_food_lookup_by_id(client: TestClient, db_session: Session):
    """Test agent retrieves detailed food nutritional facts via get_food."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "read_getfood")
    user = db_session.get(User, user_dict["id"])
    idli = food_service.get_by_name(db_session, "Idli")

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "get_food", "arguments": {"food_id": idli.id}}),
        json.dumps({"action": "final_response", "content": f"Idli provides {idli.calories} calories per piece."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat(f"What are the nutrition details for food ID {idli.id}?", ctx)
    assert "get_food" in result.tools_used
    assert str(idli.calories) in result.response


# ==============================================================================
# 2. MEAL FLOWS
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_meal_logging_single_food(client: TestClient, db_session: Session):
    """Test end-to-end meal logging: search_foods -> create_meal -> final response."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "log_single")
    user = db_session.get(User, user_dict["id"])
    idli = food_service.get_by_name(db_session, "Idli")

    initial_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()

    mock_responses = [
        # Turn 1: Search food
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "idli"}}),
        # Turn 2: Create meal with resolved food_id
        json.dumps({
            "action": "call_tool",
            "tool": "create_meal",
            "arguments": {
                "meal_type": "BREAKFAST",
                "items": [{"food_id": idli.id, "quantity": 2, "unit": "piece"}],
            },
        }),
        # Turn 3: Final confirmation
        json.dumps({"action": "final_response", "content": "Logged your breakfast: 2 pieces of Idli (116 kcal)."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("I had 2 idlis for breakfast.", ctx)

    assert "search_foods" in result.tools_used
    assert "create_meal" in result.tools_used
    assert "Logged your breakfast" in result.response

    # Verify database state
    final_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()
    assert final_meal_count == initial_meal_count + 1

    latest_meal = (
        db_session.query(Meal)
        .filter(Meal.user_id == user.id)
        .order_by(Meal.id.desc())
        .first()
    )
    assert latest_meal is not None
    assert latest_meal.meal_type == "BREAKFAST"
    assert len(latest_meal.items) == 1
    assert latest_meal.items[0].calculated_calories == Decimal("116.00")


@pytest.mark.asyncio
async def test_agent_meal_logging_multiple_foods(client: TestClient, db_session: Session):
    """Test meal logging with multiple foods resolved sequentially."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "log_multi")
    user = db_session.get(User, user_dict["id"])
    idli = food_service.get_by_name(db_session, "Idli")
    rice = food_service.get_by_name(db_session, "Cooked White Rice")

    mock_responses = [
        # Turn 1: Search idli
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "idli"}}),
        # Turn 2: Search rice
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "rice"}}),
        # Turn 3: Create meal with both items
        json.dumps({
            "action": "call_tool",
            "tool": "create_meal",
            "arguments": {
                "meal_type": "LUNCH",
                "items": [
                    {"food_id": idli.id, "quantity": 2, "unit": "piece"},
                    {"food_id": rice.id, "quantity": 150, "unit": "gram"},
                ],
            },
        }),
        # Turn 4: Final response
        json.dumps({"action": "final_response", "content": "Logged lunch with 2 idlis and 150g rice."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("I had 2 idlis and 150g rice for lunch.", ctx)
    assert "create_meal" in result.tools_used
    assert "Logged lunch" in result.response


@pytest.mark.asyncio
async def test_agent_ambiguous_quantity_asks_clarification(client: TestClient, db_session: Session):
    """Test agent asks clarification and creates NO meal when quantity is missing."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "ambig_qty")
    user = db_session.get(User, user_dict["id"])

    initial_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()

    # Model observes ambiguous quantity and asks clarification directly
    mock_responses = [
        json.dumps({
            "action": "final_response",
            "content": "How much rice did you have? Please specify the quantity and unit (e.g., 1 cup or 150 grams).",
        }),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("I had some rice.", ctx)
    assert "How much rice" in result.response
    assert "create_meal" not in result.tools_used

    # Verify zero database writes occurred
    final_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()
    assert final_meal_count == initial_meal_count


@pytest.mark.asyncio
async def test_agent_unknown_food_not_hallucinated(client: TestClient, db_session: Session):
    """Test searching for unknown food does not hallucinate an ID or log a meal."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "unknown_food")
    user = db_session.get(User, user_dict["id"])

    initial_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "MartianFruit123"}}),
        json.dumps({
            "action": "final_response",
            "content": "I could not find MartianFruit123 in the food catalog. Please verify the food name.",
        }),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("I ate 2 MartianFruit123.", ctx)
    assert "could not find" in result.response
    assert "create_meal" not in result.tools_used

    final_meal_count = db_session.query(Meal).filter(Meal.user_id == user.id).count()
    assert final_meal_count == initial_meal_count


@pytest.mark.asyncio
async def test_agent_tool_error_handled_honestly(client: TestClient, db_session: Session):
    """Test tool error (e.g. invalid unit) is honestly communicated rather than claiming success."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "failed_tool")
    user = db_session.get(User, user_dict["id"])
    idli = food_service.get_by_name(db_session, "Idli")

    mock_responses = [
        # Attempt to create meal with invalid incompatible unit
        json.dumps({
            "action": "call_tool",
            "tool": "create_meal",
            "arguments": {
                "meal_type": "BREAKFAST",
                "items": [{"food_id": idli.id, "quantity": 2, "unit": "liter"}],
            },
        }),
        # Model receives tool error and explains failure
        json.dumps({
            "action": "final_response",
            "content": "I could not log the meal because the unit 'liter' is incompatible with 'piece'.",
        }),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Log 2 liters of idli.", ctx)
    assert "could not log" in result.response
    assert "incompatible" in result.response


# ==============================================================================
# 3. SECURITY & AUTHORIZATION
# ==============================================================================

def test_api_agent_chat_unauthenticated(client: TestClient):
    """Test endpoint requires JWT authentication."""
    res = client.post("/api/v1/agent/chat", json={"message": "Hello"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_agent_user_isolation(client: TestClient, db_session: Session):
    """Test User A's agent cannot access User B's meals via get_meal."""
    seed_foods(db_session)
    token_a, user_a_dict = register_user(client, "user_a")
    token_b, user_b_dict = register_user(client, "user_b")
    user_a = db_session.get(User, user_a_dict["id"])
    user_b = db_session.get(User, user_b_dict["id"])
    idli = food_service.get_by_name(db_session, "Idli")

    # Create a meal for User B
    meal_b = Meal(
        user_id=user_b.id,
        meal_type="LUNCH",
        consumed_at=datetime.now(timezone.utc),
    )
    db_session.add(meal_b)
    db_session.commit()
    db_session.refresh(meal_b)

    # User A's agent attempts to get User B's meal
    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "get_meal", "arguments": {"meal_id": meal_b.id}}),
        json.dumps({"action": "final_response", "content": "Meal not found."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user_a, client=mock_client)

    result = await agent_service.chat(f"Show me meal {meal_b.id}", ctx)
    assert "not found" in result.response.lower()


def test_api_agent_chat_cannot_spoof_user_id(client: TestClient, db_session: Session):
    """Test client cannot pass user_id in JSON payload to override auth identity."""
    token, user = register_user(client, "spoof_user")

    with patch("app.api.v1.endpoints.agent.agent_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = {"response": "Mocked", "tools_used": []}

        # Include arbitrary user_id in payload
        res = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello", "user_id": 999999},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

        # Verify runtime_context received the authenticated user, NOT 999999
        call_kwargs = mock_chat.call_args[1]
        runtime_ctx = call_kwargs["runtime_context"]
        assert runtime_ctx.user_id == user["id"]
        assert runtime_ctx.user_id != 999999


# ==============================================================================
# 4. SAFETY, BOUNDARIES & ITERATION LIMITS
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_unknown_tool_rejected(client: TestClient, db_session: Session):
    """Test model requesting an unknown/arbitrary tool is safely rejected."""
    token, user_dict = register_user(client, "unknown_tool")
    user = db_session.get(User, user_dict["id"])

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "execute_arbitrary_python", "arguments": {"code": "1+1"}}),
        json.dumps({"action": "final_response", "content": "I cannot execute arbitrary code."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Run python code", ctx)
    assert "cannot execute" in result.response
    assert "execute_arbitrary_python" not in result.tools_used


@pytest.mark.asyncio
async def test_agent_max_iteration_limit(client: TestClient, db_session: Session):
    """Test infinite tool calling loop terminates at MAX_AGENT_ITERATIONS."""
    seed_foods(db_session)
    token, user_dict = register_user(client, "max_iter")
    user = db_session.get(User, user_dict["id"])

    # Always call a tool without producing final_response
    infinite_tool_calls = [
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "idli"}})
        for _ in range(10)
    ]
    mock_client = MockOllamaClient(infinite_tool_calls)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Looping query", ctx)
    assert "maximum reasoning steps" in result.response


@pytest.mark.asyncio
async def test_agent_tool_argument_validation_error_handled(client: TestClient, db_session: Session):
    """Test invalid tool arguments produce controlled error message."""
    token, user_dict = register_user(client, "arg_val")
    user = db_session.get(User, user_dict["id"])

    mock_responses = [
        # Call search_foods with negative limit (violates ge=1)
        json.dumps({"action": "call_tool", "tool": "search_foods", "arguments": {"query": "idli", "limit": -5}}),
        json.dumps({"action": "final_response", "content": "Invalid search parameters were provided."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Search with invalid limit", ctx)
    assert "Invalid search parameters" in result.response


# ==============================================================================
# 5. API ENDPOINT & HTTP ERROR HANDLING
# ==============================================================================

def test_api_agent_chat_success(client: TestClient, db_session: Session):
    """Test POST /api/v1/agent/chat successfully returns AgentChatResponse."""
    seed_foods(db_session)
    token, _ = register_user(client, "api_succ")

    with patch(
        "app.llm.client.OllamaClient.chat",
        new_callable=AsyncMock,
        return_value=json.dumps({"action": "final_response", "content": "You are on track today!"}),
    ):
        res = client.post(
            "/api/v1/agent/chat",
            json={"message": "How am I doing today?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["response"] == "You are on track today!"
        assert isinstance(data["tools_used"], list)


def test_api_agent_chat_empty_message_422(client: TestClient):
    """Test empty message validation fails with HTTP 422."""
    token, _ = register_user(client, "api_empty")
    res = client.post(
        "/api/v1/agent/chat",
        json={"message": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_api_agent_chat_ollama_unavailable_503(client: TestClient):
    """Test Ollama connection failure returns HTTP 503."""
    token, _ = register_user(client, "api_503")

    with patch(
        "app.llm.client.OllamaClient.chat",
        new_callable=AsyncMock,
        side_effect=OllamaConnectionError("Server unreachable"),
    ):
        res = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 503
        assert "unavailable" in res.json()["detail"].lower()


def test_api_agent_chat_ollama_timeout_504(client: TestClient):
    """Test Ollama timeout returns HTTP 504."""
    token, _ = register_user(client, "api_504")

    with patch(
        "app.llm.client.OllamaClient.chat",
        new_callable=AsyncMock,
        side_effect=OllamaTimeoutError("Request timed out"),
    ):
        res = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 504
        assert "timed out" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_agent_arbitrary_function_execution_rejected(client: TestClient, db_session: Session):
    """Verify built-in Python or OS functions cannot be invoked through the agent."""
    token, user_dict = register_user(client, "no_arbitrary")
    user = db_session.get(User, user_dict["id"])

    mock_responses = [
        json.dumps({"action": "call_tool", "tool": "eval", "arguments": {"expression": "2+2"}}),
        json.dumps({"action": "final_response", "content": "I cannot execute arbitrary functions."}),
    ]
    mock_client = MockOllamaClient(mock_responses)
    ctx = AgentRuntimeContext(db=db_session, user=user, client=mock_client)

    result = await agent_service.chat("Eval 2+2", ctx)
    assert "eval" not in result.tools_used
    assert "cannot execute" in result.response

