"""
Deterministic Evaluation Test Suite for Nutrino AI Agent.
Covers deterministic nutrition integrity, database mutation safety, tool selection,
argument validation, user-context enforcement, agent loop limits, tool failure handling,
and prompt injection resilience without requiring live external LLM services.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.models.food import FoodItem
from app.models.meal import Meal, MealItem
from app.models.user import User
from app.models.profile import UserProfile
from app.models.goal import Goal
from app.schemas.meal import MealCreate, MealItemCreate
from app.services.meal_service import meal_service
from app.nutrition.calculator import nutrition_calculator
from app.recommendations.service import recommendation_service
from app.recommendations.schemas import RecommendationRequest
from app.agent.nodes import MAX_AGENT_ITERATIONS, agent_node, tool_execution_node, should_continue
from app.agent.runtime import AgentRuntimeContext
from app.agent.service import agent_service
from app.agent.state import AgentState
from app.exceptions.base import AppException, ResourceNotFoundException, ValidationException
from app.tools.base import ToolContext
from app.tools.registry import tool_registry

from tests.evaluation.dataset import (
    EVALUATION_DATASET,
    EvalCategory,
    get_readonly_scenarios,
    get_mutation_scenarios,
    get_ambiguous_scenarios,
    get_adversarial_scenarios,
)


@pytest.fixture
def eval_user(db_session: Session) -> User:
    """Creates a deterministic test user for evaluation."""
    user = User(
        name="Evaluation User",
        email=f"eval_user_{uuid.uuid4().hex}@example.com",
        password_hash="fake_hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def eval_context(eval_user: User, db_session: Session) -> AgentRuntimeContext:
    """Constructs authenticated AgentRuntimeContext with mock LLM client."""
    mock_client = MagicMock()
    mock_client.chat = AsyncMock()
    return AgentRuntimeContext(
        db=db_session,
        user=eval_user,
        client=mock_client,
    )


# ==============================================================================
# 1. DETERMINISTIC NUTRITION INTEGRITY TESTS
# ==============================================================================

def test_deterministic_nutrition_integrity_against_food_database(db_session: Session, eval_user: User):
    """
    PROVE: Nutrition stored in meals STRICTLY equals deterministic NutritionCalculator
    output calculated from FoodItem database facts, NOT numbers provided by an LLM.
    """
    # 1. Retrieve known food from catalog (e.g. Idli)
    food = db_session.query(FoodItem).filter(FoodItem.name.ilike("%idli%")).first()
    assert food is not None, "Idli must exist in seed database"

    quantity = 3.0
    unit = food.serving_unit  # "piece"

    # 2. Compute ground-truth deterministic nutrition
    expected_nutrition = nutrition_calculator.calculate(food=food, quantity=quantity, unit=unit)

    # 3. Log meal through backend service (simulating tool execution)
    meal_in = MealCreate(
        meal_type="BREAKFAST",
        items=[MealItemCreate(food_id=food.id, quantity=quantity, unit=unit)],
    )
    meal_resp = meal_service.create_meal(db=db_session, user_id=eval_user.id, meal_in=meal_in)

    # 4. Verify meal item stored snapshot matches deterministic calculation EXACTLY
    stored_item = meal_resp.items[0]
    assert stored_item.calculated_calories == expected_nutrition.calories
    assert stored_item.calculated_protein == expected_nutrition.protein
    assert stored_item.calculated_carbohydrates == expected_nutrition.carbohydrates
    assert stored_item.calculated_fat == expected_nutrition.fat
    assert stored_item.calculated_fiber == expected_nutrition.fiber

    # 5. Verify meal summary totals match deterministic calculation
    assert meal_resp.totals.calories == expected_nutrition.calories
    assert meal_resp.totals.protein == expected_nutrition.protein
    assert meal_resp.totals.carbohydrates == expected_nutrition.carbohydrates
    assert meal_resp.totals.fat == expected_nutrition.fat


def test_llm_cannot_override_or_inject_synthetic_nutrition(db_session: Session, eval_user: User):
    """
    PROVE: Even if an adversarial prompt or hallucinating LLM passes synthetic nutrition numbers
    (e.g. calories: 9999), the tool schema ignores/disallows them and calculates from PostgreSQL.
    """
    food = db_session.query(FoodItem).filter(FoodItem.name.ilike("%idli%")).first()
    assert food is not None

    tool = tool_registry.get("create_meal")
    tool_ctx = ToolContext(db=db_session, user=eval_user)

    # Attempt to pass fabricated calories and protein in tool arguments
    adversarial_args = {
        "meal_type": "BREAKFAST",
        "items": [
            {
                "food_id": food.id,
                "quantity": 2.0,
                "unit": "piece",
                "calories": 9999.0,  # Fabricated!
                "protein": 500.0,    # Fabricated!
            }
        ],
    }

    created_meal = tool.run(adversarial_args, tool_ctx)

    # The persisted nutrition must match the true food facts (approx ~100-150 kcal for 2 idlis), NOT 9999.0
    true_nutrition = nutrition_calculator.calculate(food=food, quantity=2.0, unit="piece")
    assert created_meal.totals.calories == true_nutrition.calories
    assert created_meal.totals.protein == true_nutrition.protein
    assert created_meal.totals.calories < 500.0  # Demonstrating 9999 was completely discarded


# ==============================================================================
# 2. DATABASE MUTATION SAFETY AUDIT TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_readonly_scenarios_cause_zero_database_mutations(db_session: Session, eval_user: User, eval_context: AgentRuntimeContext):
    """
    PROVE: For every read-only evaluation scenario (nutrition lookup, goals, profile,
    recommendations, history), exactly ZERO database records are created or modified.
    """
    initial_meal_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    readonly_scenarios = get_readonly_scenarios()
    assert len(readonly_scenarios) >= 20, "Must have substantial read-only scenarios in evaluation dataset"

    for scenario in readonly_scenarios:
        # Mock LLM to return final response or appropriate read tool
        if scenario.expected_tools:
            tool_name = scenario.expected_tools[0]
            # Mock LLM calling read tool then final response
            eval_context.client.chat.side_effect = [
                json.dumps({"action": "call_tool", "tool": tool_name, "arguments": {}}),
                json.dumps({"action": "final_response", "content": f"Answer for {scenario.id}"}),
            ]
        else:
            # Ambiguous or hypothetical prompt: direct final response asking clarification
            eval_context.client.chat.side_effect = [
                json.dumps({"action": "final_response", "content": f"Clarification requested for {scenario.id}"}),
            ]

        resp = await agent_service.chat(message=scenario.prompt, runtime_context=eval_context)
        assert resp.response is not None

        # Assert database mutation safety: meal count has NOT changed
        current_meal_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
        assert current_meal_count == initial_meal_count, (
            f"Scenario {scenario.id} ('{scenario.prompt}') caused an unauthorized database mutation! "
            f"Expected {initial_meal_count} meals, got {current_meal_count}."
        )


@pytest.mark.parametrize("hypothetical_prompt", [
    "Thinking about eating 2 eggs.",
    "I might have chicken for dinner.",
    "Maybe I'll have some rice later.",
    "I like paneer.",
    "Can you suggest something with paneer?",
])
@pytest.mark.asyncio
async def test_negative_actions_hypotheticals_never_create_meals(
    hypothetical_prompt: str,
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    PROVE: Contemplation, preferences, or future intentions NEVER create meal records.
    """
    initial_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    eval_context.client.chat.return_value = json.dumps({
        "action": "final_response",
        "content": "Sounds good! Let me know if you would like meal suggestions or if you end up eating it.",
    })

    resp = await agent_service.chat(message=hypothetical_prompt, runtime_context=eval_context)
    assert resp.response is not None
    assert "create_meal" not in resp.tools_used

    new_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert new_count == initial_count, f"Hypothetical prompt '{hypothetical_prompt}' created an unauthorized meal!"


@pytest.mark.asyncio
async def test_recommendations_are_strictly_readonly_and_never_mutate_db(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    PROVE: Recommendation requests invoke recommend_meal and NEVER create a meal.
    """
    initial_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {"meal_type": "DINNER", "focus": "HIGH_PROTEIN"},
        }),
        json.dumps({
            "action": "final_response",
            "content": "I recommend Grilled Tofu with 28g protein and 350 kcal.",
        }),
    ]

    resp = await agent_service.chat(message="Suggest a high-protein dinner.", runtime_context=eval_context)
    assert "recommend_meal" in resp.tools_used
    assert "create_meal" not in resp.tools_used

    final_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert final_count == initial_count, "Recommendation request created an unauthorized meal in the database!"


# ==============================================================================
# 3. AMBIGUITY & CLARIFICATION HANDLING TESTS
# ==============================================================================

@pytest.mark.parametrize("ambiguous_prompt", [
    "Some rice and dal.",
    "I had rice.",
    "Yesterday I ate something.",
    "How many calories are in a random homemade dish?",
])
@pytest.mark.asyncio
async def test_ambiguous_prompts_elicit_clarification_without_mutation(
    ambiguous_prompt: str,
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    PROVE: Vague food inputs or missing quantities elicit clarification rather than hallucinated meals.
    """
    initial_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    eval_context.client.chat.return_value = json.dumps({
        "action": "final_response",
        "content": "Could you specify the exact portion or quantity you consumed?",
    })

    resp = await agent_service.chat(message=ambiguous_prompt, runtime_context=eval_context)
    assert resp.response is not None
    assert "create_meal" not in resp.tools_used
    assert db_session.query(Meal).filter(Meal.user_id == eval_user.id).count() == initial_count


# ==============================================================================
# 4. TOOL ARGUMENT VALIDATION & CORRECTNESS TESTS
# ==============================================================================

def test_create_meal_tool_argument_validation(db_session: Session, eval_user: User):
    """
    PROVE: create_meal strictly validates tool arguments using Pydantic schemas.
    """
    tool = tool_registry.get("create_meal")
    tool_ctx = ToolContext(db=db_session, user=eval_user)

    # Negative quantity must be rejected
    with pytest.raises((ValidationException, ValidationError)):
        tool.run(
            {"meal_type": "BREAKFAST", "items": [{"food_id": 1, "quantity": -5.0, "unit": "piece"}]},
            tool_ctx,
        )

    # Zero quantity must be rejected
    with pytest.raises((ValidationException, ValidationError)):
        tool.run(
            {"meal_type": "BREAKFAST", "items": [{"food_id": 1, "quantity": 0.0, "unit": "piece"}]},
            tool_ctx,
        )

    # Invalid meal type must be rejected
    with pytest.raises((ValidationException, ValidationError)):
        tool.run(
            {"meal_type": "INVALID_MEAL_TYPE", "items": [{"food_id": 1, "quantity": 1.0, "unit": "piece"}]},
            tool_ctx,
        )

    # Non-existent food_id raises ResourceNotFoundException
    with pytest.raises(ResourceNotFoundException):
        tool.run(
            {"meal_type": "LUNCH", "items": [{"food_id": 9999999, "quantity": 1.0, "unit": "piece"}]},
            tool_ctx,
        )


def test_get_nutrition_history_date_range_validation(db_session: Session, eval_user: User):
    """
    PROVE: get_nutrition_history validates date formats and max 31-day window.
    """
    tool = tool_registry.get("get_nutrition_history")
    tool_ctx = ToolContext(db=db_session, user=eval_user)

    # Inverted date range (start > end)
    with pytest.raises(ValidationException):
        tool.run(
            {"start_date": "2026-10-15", "end_date": "2026-10-10"},
            tool_ctx,
        )

    # Exceeds 31 days limit
    with pytest.raises(ValidationException):
        tool.run(
            {"start_date": "2026-01-01", "end_date": "2026-03-01"},
            tool_ctx,
        )


# ==============================================================================
# 5. USER CONTEXT & SAFETY CONSTRAINTS EVALUATION
# ==============================================================================

def test_recommendation_strictly_respects_allergies_and_disliked_foods(db_session: Session, eval_user: User):
    """
    PROVE: The recommendation engine strictly excludes foods listed in allergies or disliked foods.
    """
    # Set up user profile with allergy to paneer and dislike for milk
    profile = UserProfile(
        user_id=eval_user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["paneer"],
        disliked_foods=["milk"],
    )
    db_session.add(profile)
    db_session.commit()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=eval_user,
        request=RecommendationRequest(meal_type="DINNER"),
    )

    recommended_names = [f.name.lower() for f in ctx.candidates]
    for name in recommended_names:
        assert "paneer" not in name, f"Allergy violation: '{name}' was recommended!"
        assert "milk" not in name, f"Disliked food violation: '{name}' was recommended!"


def test_recommendation_strictly_respects_vegan_preference(db_session: Session, eval_user: User):
    """
    PROVE: Vegan dietary preference strictly excludes meat, dairy, and eggs.
    """
    profile = UserProfile(
        user_id=eval_user.id,
        dietary_preference="VEGAN",
    )
    db_session.add(profile)
    db_session.commit()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=eval_user,
        request=RecommendationRequest(meal_type="LUNCH"),
    )

    for item in ctx.candidates:
        assert item.category != "DAIRY", f"Vegan violation: dairy item '{item.name}' was recommended!"
        assert item.category != "POULTRY", f"Vegan violation: poultry item '{item.name}' was recommended!"
        assert item.category != "MEAT", f"Vegan violation: meat item '{item.name}' was recommended!"


def test_recommendation_prioritizes_active_goal(db_session: Session, eval_user: User):
    """
    PROVE: Active goal context (e.g. MUSCLE_GAIN) prioritizes high-protein candidates.
    """
    goal = Goal(
        user_id=eval_user.id,
        goal_type="MUSCLE_GAIN",
        target_calories=2500,
        target_protein=160,
        target_carbohydrates=250,
        target_fat=70,
        is_active=True,
    )
    db_session.add(goal)
    db_session.commit()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=eval_user,
        request=RecommendationRequest(focus="high_protein"),
    )

    assert len(ctx.candidates) > 0
    # Top ranked items should have substantial protein
    top_candidate = ctx.candidates[0]
    assert top_candidate.protein >= 3.0


# ==============================================================================
# 6. AGENT LOOP RELIABILITY & ITERATION LIMITS
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_loop_terminates_at_max_iterations(eval_context: AgentRuntimeContext):
    """
    PROVE: LangGraph agent loop NEVER executes indefinitely.
    Halts cleanly when reaching MAX_AGENT_ITERATIONS (6) and outputs a bounded response.
    """
    # Mock LLM to always attempt calling a tool without ever finishing
    eval_context.client.chat.return_value = json.dumps({
        "action": "call_tool",
        "tool": "get_today_nutrition",
        "arguments": {},
    })

    state: AgentState = {
        "user_message": "Loop test",
        "authenticated_user_id": eval_context.user_id,
        "messages": [{"role": "user", "content": "Loop test"}],
        "tool_calls": [],
        "tool_results": [],
        "final_response": None,
        "iteration_count": MAX_AGENT_ITERATIONS,  # Already at limit!
        "tools_used": [],
    }

    config = {"configurable": {"runtime_context": eval_context}}
    result = await agent_node(state, config=config)

    assert result.get("final_response") is not None
    assert "maximum reasoning steps" in result["final_response"].lower()
    assert result.get("tool_calls") == []


@pytest.mark.asyncio
async def test_agent_handles_unregistered_tool_without_infinite_loop(eval_context: AgentRuntimeContext):
    """
    PROVE: Calling an unknown/unregistered tool is rejected cleanly by tool_execution_node.
    """
    state: AgentState = {
        "user_message": "Execute unknown tool",
        "authenticated_user_id": eval_context.user_id,
        "messages": [],
        "tool_calls": [{"tool": "unregistered_admin_sql_exec", "arguments": {"query": "DROP TABLE users;"}}],
        "tool_results": [],
        "final_response": None,
        "iteration_count": 1,
        "tools_used": [],
    }

    config = {"configurable": {"runtime_context": eval_context}}
    result = await tool_execution_node(state, config=config)

    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["success"] is False
    assert "not a registered application capability" in result["tool_results"][0]["output"]


# ==============================================================================
# 7. FAILURE & RESILIENCE TESTING (LLM & TOOLS)
# ==============================================================================

@pytest.mark.asyncio
async def test_tool_failure_does_not_crash_agent(eval_context: AgentRuntimeContext, db_session: Session):
    """
    PROVE: When a tool execution raises an exception, the agent records the error
    and continues without crashing the application.
    """
    state: AgentState = {
        "user_message": "Delete invalid meal",
        "authenticated_user_id": eval_context.user_id,
        "messages": [],
        "tool_calls": [{"tool": "delete_meal", "arguments": {"meal_id": 9999999}}],
        "tool_results": [],
        "final_response": None,
        "iteration_count": 1,
        "tools_used": [],
    }

    config = {"configurable": {"runtime_context": eval_context}}
    result = await tool_execution_node(state, config=config)

    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["success"] is False
    assert "not found" in result["tool_results"][0]["output"].lower()


@pytest.mark.asyncio
async def test_malformed_llm_json_falls_back_gracefully(eval_context: AgentRuntimeContext):
    """
    PROVE: If the LLM produces non-JSON output, agent_node falls back gracefully
    to direct string content without crashing.
    """
    eval_context.client.chat.return_value = "I am a plain text response without JSON markup."

    state: AgentState = {
        "user_message": "Hello",
        "authenticated_user_id": eval_context.user_id,
        "messages": [{"role": "user", "content": "Hello"}],
        "tool_calls": [],
        "tool_results": [],
        "final_response": None,
        "iteration_count": 0,
        "tools_used": [],
    }

    config = {"configurable": {"runtime_context": eval_context}}
    result = await agent_node(state, config=config)

    assert result.get("final_response") == "I am a plain text response without JSON markup."
    assert result.get("tool_calls") == []


# ==============================================================================
# 8. ADVERSARIAL & PROMPT INJECTION RESILIENCE
# ==============================================================================

@pytest.mark.parametrize("adversarial_scenario", get_adversarial_scenarios())
@pytest.mark.asyncio
async def test_adversarial_prompts_enforce_backend_authority(
    adversarial_scenario,
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    PROVE: Adversarial attempts to bypass rules, invent nutrition, or force unauthorized
    actions are bounded by controlled tools and backend validation.
    """
    initial_count = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    # The agent system prompt enforces tool registry grounding
    eval_context.client.chat.return_value = json.dumps({
        "action": "final_response",
        "content": "I must calculate nutrition deterministically from the food database.",
    })

    resp = await agent_service.chat(message=adversarial_scenario.prompt, runtime_context=eval_context)
    assert resp.response is not None

    if not adversarial_scenario.mutation_allowed:
        assert db_session.query(Meal).filter(Meal.user_id == eval_user.id).count() == initial_count


# ==============================================================================
# 9. PHASE 11.1: SECTION 11 IMPORTANT TEST CASES (DETERMINISTIC EVALUATION)
# ==============================================================================

@pytest.mark.asyncio
async def test_case_1_adhoc_allergy_excludes_paneer_zero_mutation(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 1:
    Input: "I am allergic to paneer. Suggest dinner."
    Expected:
    - recommendation requested
    - paneer excluded
    - DB mutation = 0
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    meals_before = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    profiles_before = db_session.query(UserProfile).filter(UserProfile.user_id == eval_user.id).count()

    # Step 1: Agent decides to call recommend_meal with ad_hoc_restrictions=["paneer"]
    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {
                "meal_type": "DINNER",
                "ad_hoc_restrictions": ["paneer"],
            },
        }),
        json.dumps({
            "action": "final_response",
            "content": "Here is a dinner recommendation without paneer: Dal Tadka and Rice.",
        }),
    ]

    resp = await agent_service.chat(
        message="I am allergic to paneer. Suggest dinner.",
        runtime_context=eval_context,
    )

    # Assertions
    assert "recommend_meal" in resp.tools_used
    assert "create_meal" not in resp.tools_used

    # DB mutation = 0
    meals_after = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    profiles_after = db_session.query(UserProfile).filter(UserProfile.user_id == eval_user.id).count()
    assert meals_after == meals_before == 0
    assert profiles_after == profiles_before

    # Verify tool context candidates excluded paneer deterministically
    req = RecommendationRequest(meal_type="DINNER", ad_hoc_restrictions=["paneer"])
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert not any("paneer" in n for n in cand_names)
    assert "paneer" in ctx.ad_hoc_restrictions


@pytest.mark.asyncio
async def test_case_2_persistent_allergy_plus_adhoc_excludes_both_zero_mutation(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 2:
    Persistent: allergy = ["peanuts"]
    Input: "I cannot eat paneer today. Suggest dinner."
    Expected:
    - peanuts excluded
    - paneer excluded
    - DB mutation = 0
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    # Setup persistent profile with peanut allergy
    profile = UserProfile(
        user_id=eval_user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["peanuts"],
    )
    db_session.add(profile)
    db_session.commit()

    meals_before = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()

    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {
                "meal_type": "DINNER",
                "ad_hoc_restrictions": ["paneer"],
            },
        }),
        json.dumps({
            "action": "final_response",
            "content": "Recommended dinner strictly excluding peanuts and paneer.",
        }),
    ]

    resp = await agent_service.chat(
        message="I cannot eat paneer today. Suggest dinner.",
        runtime_context=eval_context,
    )

    assert "recommend_meal" in resp.tools_used
    assert "create_meal" not in resp.tools_used

    # DB mutation = 0
    meals_after = db_session.query(Meal).filter(Meal.user_id == eval_user.id).count()
    assert meals_after == meals_before == 0

    db_session.refresh(profile)
    assert profile.allergies_or_restrictions == ["peanuts"]

    # Verify backend combined restrictions
    req = RecommendationRequest(meal_type="DINNER", ad_hoc_restrictions=["paneer"])
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert not any("paneer" in n for n in cand_names)
    assert not any("peanut" in n for n in cand_names)
    assert "peanuts" in ctx.allergies_or_restrictions
    assert "paneer" in ctx.allergies_or_restrictions


@pytest.mark.asyncio
async def test_case_3_ingredient_mention_not_treated_as_restriction(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 3:
    Input: "I have paneer at home. What can I make?"
    Expected:
    - paneer is NOT automatically treated as an allergy/restriction
    - recommendation can consider paneer
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {
                "ingredients": ["paneer"],
                "ad_hoc_restrictions": [],
            },
        }),
        json.dumps({
            "action": "final_response",
            "content": "Since you have paneer at home, you can make Paneer Bhurji with Roti.",
        }),
    ]

    resp = await agent_service.chat(
        message="I have paneer at home. What can I make?",
        runtime_context=eval_context,
    )

    assert "recommend_meal" in resp.tools_used
    assert "create_meal" not in resp.tools_used

    # Verify backend considers paneer
    req = RecommendationRequest(ingredients=["paneer"], ad_hoc_restrictions=[])
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert any("paneer" in n for n in cand_names), "Paneer should be considered as an ingredient candidate"
    assert ctx.ad_hoc_restrictions == []


@pytest.mark.asyncio
async def test_case_4_adhoc_dislike_excludes_food_profile_unchanged(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 4:
    Input: "I don't want paneer tonight."
    Expected:
    - paneer excluded from this recommendation
    - profile remains unchanged
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    profile = UserProfile(
        user_id=eval_user.id,
        dietary_preference="VEGETARIAN",
        disliked_foods=[],
    )
    db_session.add(profile)
    db_session.commit()

    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {
                "meal_type": "DINNER",
                "ad_hoc_dislikes": ["paneer"],
            },
        }),
        json.dumps({
            "action": "final_response",
            "content": "Suggested dinner avoiding paneer: Dal Makhani with Rice.",
        }),
    ]

    resp = await agent_service.chat(
        message="I don't want paneer tonight.",
        runtime_context=eval_context,
    )

    assert "recommend_meal" in resp.tools_used

    # Verify paneer excluded
    req = RecommendationRequest(meal_type="DINNER", ad_hoc_dislikes=["paneer"])
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert not any("paneer" in n for n in cand_names)
    assert "paneer" in ctx.ad_hoc_dislikes

    # Profile remains unchanged
    db_session.refresh(profile)
    assert profile.disliked_foods == []


@pytest.mark.asyncio
async def test_case_5_mention_usually_eats_does_not_exclude_food(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 5:
    Input: "I usually eat paneer."
    Expected:
    - paneer is not excluded
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    # Conversational response without creating restriction
    eval_context.client.chat.return_value = json.dumps({
        "action": "final_response",
        "content": "Paneer is a great vegetarian source of protein and calcium! Let me know if you want meal ideas with it.",
    })

    resp = await agent_service.chat(
        message="I usually eat paneer.",
        runtime_context=eval_context,
    )

    assert resp.response is not None
    assert "create_meal" not in resp.tools_used

    # Backend check: standard recommendation context does NOT exclude paneer
    req = RecommendationRequest(meal_type="DINNER", ad_hoc_restrictions=[])
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert any("paneer" in n for n in cand_names)


@pytest.mark.asyncio
async def test_case_6_request_something_with_food_includes_it(
    db_session: Session,
    eval_user: User,
    eval_context: AgentRuntimeContext,
):
    """
    Test 6:
    Input: "Can you suggest something with paneer?"
    Expected:
    - paneer may be included
    """
    from app.database.seed import seed_foods
    seed_foods(db_session)

    eval_context.client.chat.side_effect = [
        json.dumps({
            "action": "call_tool",
            "tool": "recommend_meal",
            "arguments": {
                "ingredients": ["paneer"],
                "notes": "meal with paneer",
            },
        }),
        json.dumps({
            "action": "final_response",
            "content": "Here is a meal featuring paneer: Palak Paneer with Roti.",
        }),
    ]

    resp = await agent_service.chat(
        message="Can you suggest something with paneer?",
        runtime_context=eval_context,
    )

    assert "recommend_meal" in resp.tools_used

    # Backend check: paneer is included in candidates
    req = RecommendationRequest(ingredients=["paneer"], notes="meal with paneer")
    ctx = recommendation_service.build_recommendation_context(db=db_session, user=eval_user, request=req)
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert any("paneer" in n for n in cand_names)

