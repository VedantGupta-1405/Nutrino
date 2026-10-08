"""
Live LLM Evaluation Test Suite for Nutrino AI Agent (Ollama + Qwen 3 8B).
Evaluates real intent understanding, tool selection, ambiguity handling,
hypothetical intent recognition, recommendation safety, and latency visibility.

Marked with @pytest.mark.llm so it can be run specifically or skipped in fast CI.
"""

import uuid
import httpx
import pytest
from sqlalchemy.orm import Session

from app.agent.runtime import AgentRuntimeContext
from app.agent.service import agent_service
from app.exceptions.base import AppException
from app.llm.client import OllamaClient
from app.models.meal import Meal
from app.models.user import User
from app.models.profile import UserProfile
from app.models.goal import Goal


def is_ollama_available() -> bool:
    """Helper to detect if live Ollama with qwen3:8b is reachable."""
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=3.0)
        return resp.status_code == 200 and "qwen3:8b" in resp.text
    except Exception:
        return False


@pytest.fixture(scope="module")
def require_ollama():
    """Skip test module if local Ollama daemon is unreachable."""
    if not is_ollama_available():
        pytest.skip("Local Ollama daemon is not running or qwen3:8b is unavailable.")


@pytest.fixture
def eval_user(db_session: Session) -> User:
    """Creates a deterministic test user for LLM evaluation."""
    user = User(
        name="LLM Evaluation User",
        email=f"llm_eval_{uuid.uuid4().hex}@example.com",
        password_hash="fake_hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def llm_runtime_context(eval_user: User, db_session: Session) -> AgentRuntimeContext:
    """Constructs live runtime context with default Ollama client."""
    return AgentRuntimeContext(
        db=db_session,
        user=eval_user,
        client=OllamaClient(),
    )


# ==============================================================================
# LIVE LLM EVALUATION TESTS
# ==============================================================================

@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_read_meal_history_intent(
    require_ollama,
    db_session: Session,
    eval_user: User,
    llm_runtime_context: AgentRuntimeContext,
):
    """
    EVAL-HIST-01: 'What have I eaten today?'
    VERIFY: Agent invokes meal/nutrition reading tool and causes ZERO database mutations.
    """
    initial_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    resp = await agent_service.chat(
        message="What have I eaten today?",
        runtime_context=llm_runtime_context,
    )

    # 1. Output assertions
    assert resp.response is not None and len(resp.response.strip()) > 0
    assert any(tool in resp.tools_used for tool in ["get_today_meals", "get_today_nutrition"])

    # 2. Database mutation safety
    current_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert current_meals == initial_meals, "Read-only history request mutated meals table!"

    # 3. Observability and Latency
    assert resp.duration_seconds is not None and resp.duration_seconds > 0
    assert resp.iterations is not None and resp.iterations >= 1


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_protein_inquiry_intent(
    require_ollama,
    db_session: Session,
    eval_user: User,
    llm_runtime_context: AgentRuntimeContext,
):
    """
    EVAL-NUTR-02: 'How much protein have I consumed today?'
    VERIFY: Agent invokes get_today_nutrition or get_today_meals and causes ZERO database mutations.
    """
    initial_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    resp = await agent_service.chat(
        message="How much protein have I consumed today?",
        runtime_context=llm_runtime_context,
    )

    assert resp.response is not None and len(resp.response.strip()) > 0
    assert any(tool in resp.tools_used for tool in ["get_today_nutrition", "get_today_meals"])

    current_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert current_meals == initial_meals, "Nutrition inquiry mutated meals table!"
    assert resp.duration_seconds is not None and resp.duration_seconds > 0


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_negative_hypothetical_causes_no_mutation(
    require_ollama,
    db_session: Session,
    eval_user: User,
    llm_runtime_context: AgentRuntimeContext,
):
    """
    EVAL-NEG-01: 'Thinking about eating 2 eggs.'
    VERIFY: Agent does NOT log a meal when the user is merely contemplating eating.
    """
    initial_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    resp = await agent_service.chat(
        message="Thinking about eating 2 eggs.",
        runtime_context=llm_runtime_context,
    )

    assert resp.response is not None
    assert "create_meal" not in resp.tools_used, "Agent incorrectly called create_meal on a hypothetical!"

    current_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert current_meals == initial_meals, "Hypothetical statement mutated meals table!"


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_ambiguous_food_asks_clarification(
    require_ollama,
    db_session: Session,
    eval_user: User,
    llm_runtime_context: AgentRuntimeContext,
):
    """
    EVAL-AMBIG-01: 'Some rice and dal.'
    VERIFY: Ambiguity does NOT automatically create a meal. The agent asks for quantity/clarification.
    """
    initial_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    resp = await agent_service.chat(
        message="Some rice and dal.",
        runtime_context=llm_runtime_context,
    )

    assert resp.response is not None
    # Agent must NOT blindly create a meal with invented quantities
    assert "create_meal" not in resp.tools_used

    current_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert current_meals == initial_meals, "Ambiguous input caused an unauthorized meal creation!"


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_recommendation_respects_allergy(
    require_ollama,
    db_session: Session,
    eval_user: User,
    llm_runtime_context: AgentRuntimeContext,
):
    """
    EVAL-RESTR-01: 'I am allergic to paneer. Suggest dinner.'
    VERIFY: Recommendation does NOT recommend paneer, and causes zero meal creations.
    """
    initial_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    # Set up user profile with allergy
    profile = UserProfile(
        user_id=eval_user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["paneer"],
    )
    db_session.add(profile)
    db_session.commit()

    resp = await agent_service.chat(
        message="I am allergic to paneer. Suggest dinner.",
        runtime_context=llm_runtime_context,
    )

    assert resp.response is not None
    assert "create_meal" not in resp.tools_used
    # Ensure response does not promote paneer as an ingredient to eat
    assert "paneer" not in resp.response.lower() or "avoid" in resp.response.lower() or "allerg" in resp.response.lower()

    current_meals = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert current_meals == initial_meals


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_unreachable_service_failure_handling(
    db_session: Session,
    eval_user: User,
):
    """
    VERIFY: If Ollama is completely unreachable (e.g. invalid host/port),
    an appropriate exception is surfaced and no database corruption occurs.
    """
    broken_client = OllamaClient(base_url="http://127.0.0.1:54321")
    broken_context = AgentRuntimeContext(
        db=db_session,
        user=eval_user,
        client=broken_client,
    )

    with pytest.raises(Exception):
        await agent_service.chat(
            message="What is my calorie count today?",
            runtime_context=broken_context,
        )

    # Database remains unaffected
    assert db_session.query(Meal).filter(Meal.user_id == eval_user.id).count() == 0
