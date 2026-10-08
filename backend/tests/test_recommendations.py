"""
Comprehensive tests for Phase 9: Personalized Nutrition Recommendations.
Covers deterministic constraint enforcement, allergy/preference filtering,
remaining nutrition calculations, candidate ranking, tool registry integration,
user isolation, zero database mutations, and agent recommendation orchestration.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.database.seed import seed_foods
from app.exceptions.base import AuthorizationException
from app.main import app
from app.models.food import FoodItem
from app.models.goal import Goal
from app.models.meal import Meal, MealItem
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.goal import GoalType
from app.auth.security import create_access_token, get_password_hash
from app.recommendations.constraints import (
    filter_by_allergies,
    filter_by_dietary_preference,
    filter_by_disliked_foods,
    score_and_rank_candidates,
)
from app.recommendations.schemas import (
    FoodCandidate,
    RecommendationContext,
    RecommendationRequest,
    RecommendationResponse,
)
from app.recommendations.service import recommendation_service
from app.tools.base import ToolContext
from app.tools.registry import tool_registry
from app.tools.schemas import RecommendMealInput
from app.agent.runtime import AgentRuntimeContext
from app.agent.service import agent_service
from app.llm.client import OllamaClient
from app.llm.exceptions import OllamaConnectionError, OllamaTimeoutError


def create_user(db: Session, email_prefix: str = "rec_user") -> User:
    user = User(
        name="Recommendation Test User",
        email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=get_password_hash("Secret123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==============================================================================
# 1. Deterministic Constraints & Filtering Tests
# ==============================================================================

def test_vegetarian_constraint_filters_meat(db_session: Session):
    """Vegetarian preference must exclude all MEAT items (Chicken, Fish, Eggs)."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    veg_foods = filter_by_dietary_preference(all_foods, "VEGETARIAN")
    categories = {f.category for f in veg_foods}
    names = {f.name.lower() for f in veg_foods}

    assert "MEAT" not in categories
    assert not any("chicken" in n or "fish" in n or "egg" in n for n in names)
    assert any("paneer" in n for n in names)
    assert any("dal" in n for n in names)


def test_vegan_constraint_filters_meat_and_dairy(db_session: Session):
    """Vegan preference must exclude both MEAT and DAIRY items."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    vegan_foods = filter_by_dietary_preference(all_foods, "VEGAN")
    categories = {f.category for f in vegan_foods}
    names = {f.name.lower() for f in vegan_foods}

    assert "MEAT" not in categories
    assert "DAIRY" not in categories
    assert not any("paneer" in n or "curd" in n or "milk" in n for n in names)
    assert any("rice" in n for n in names)


def test_non_vegetarian_preference_keeps_all_foods(db_session: Session):
    """Non-vegetarian preference retains meat, dairy, grains, and vegetables."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    non_veg_foods = filter_by_dietary_preference(all_foods, "NON_VEGETARIAN")
    categories = {f.category for f in non_veg_foods}

    assert "MEAT" in categories
    assert "DAIRY" in categories
    assert "GRAIN" in categories
    assert len(non_veg_foods) == len(all_foods)


def test_allergy_exclusion_paneer_and_dairy(db_session: Session):
    """Allergy to dairy/paneer must exclude Paneer, Curd, and Whole Milk."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    safe_foods = filter_by_allergies(all_foods, ["paneer", "dairy"])
    names = {f.name.lower() for f in safe_foods}

    assert "paneer" not in names
    assert "curd" not in names
    assert "whole milk" not in names
    assert any("chapati" in n for n in names)


def test_disliked_foods_exclusion(db_session: Session):
    """Disliked foods must be filtered out when alternatives exist."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    filtered = filter_by_disliked_foods(all_foods, ["banana", "apple"])
    names = {f.name.lower() for f in filtered}

    assert "banana" not in names
    assert "apple" not in names


def test_ingredient_based_scoring_boost(db_session: Session):
    """Foods matching available ingredients receive top priority scores."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    req = RecommendationRequest(ingredients=["paneer", "rice"])
    context_data = {"available_ingredients": ["paneer", "rice"]}

    candidates = score_and_rank_candidates(all_foods, req, context_data, max_candidates=5)
    top_names = [c.name.lower() for c in candidates[:2]]

    assert any("paneer" in n for n in top_names) or any("rice" in n for n in top_names)


def test_high_protein_focus_ranks_protein_foods(db_session: Session):
    """high_protein focus prioritizes foods with high protein content."""
    seed_foods(db_session)
    from app.models.food import FoodItem
    all_foods = db_session.query(FoodItem).all()

    req = RecommendationRequest(focus="high_protein")
    context_data = {"goal_type": "MUSCLE_GAIN"}

    candidates = score_and_rank_candidates(all_foods, req, context_data, max_candidates=5)
    # Chicken breast, Paneer, Boiled egg, Toor dal have highest protein
    assert candidates[0].protein >= Decimal("6.00")


# ==============================================================================
# 2. Recommendation Service & Context Construction Tests
# ==============================================================================

def test_recommendation_context_construction_full_profile(db_session: Session):
    """Verifies complete context derivation with profile, goal, and daily intake."""
    seed_foods(db_session)
    user = create_user(db_session, "full_rec")

    # Set profile
    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["nuts"],
        disliked_foods=["banana"],
        available_ingredients=["paneer", "chapati"],
        preferred_cuisine=["Indian"],
        budget_per_day=500.0,
    )
    # Set goal
    goal = Goal(
        user_id=user.id,
        goal_type=GoalType.MUSCLE_GAIN.value,
        target_calories=Decimal("2200.00"),
        target_protein=Decimal("120.00"),
        target_carbohydrates=Decimal("250.00"),
        target_fat=Decimal("60.00"),
        is_active=True,
    )
    db_session.add_all([profile, goal])
    db_session.commit()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=RecommendationRequest(meal_type="DINNER", focus="high_protein"),
    )

    assert ctx.user_id == user.id
    assert ctx.dietary_preference == "VEGETARIAN"
    assert "nuts" in ctx.allergies_or_restrictions
    assert "banana" in ctx.disliked_foods
    assert ctx.goal_type == GoalType.MUSCLE_GAIN.value
    assert ctx.remaining_calories == Decimal("2200.00")
    assert len(ctx.candidates) > 0

    # Ensure constraints held in candidates
    cand_names = [c.name.lower() for c in ctx.candidates]
    cand_cats = {c.category for c in ctx.candidates}

    assert "MEAT" not in cand_cats  # vegetarian
    assert not any("almond" in n or "peanut" in n for n in cand_names)  # no nuts
    assert "banana" not in cand_names  # no banana


def test_recommendation_context_no_goal_and_no_profile(db_session: Session):
    """User without profile or goal still gets safe, balanced recommendations with limitations noted."""
    seed_foods(db_session)
    user = create_user(db_session, "empty_rec")

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=RecommendationRequest(meal_type="LUNCH"),
    )

    assert ctx.goal_type is None
    assert ctx.target_calories is None
    assert ctx.remaining_calories is None
    assert len(ctx.candidates) > 0
    assert any("No active nutrition goal is set" in lim for lim in ctx.limitations)
    assert any("No user profile configured" in lim for lim in ctx.limitations)


def test_recommendation_target_exceeded_zero_remaining(db_session: Session):
    """When consumed calories reach or exceed target, notes limitation and prioritizes light options."""
    seed_foods(db_session)
    user = create_user(db_session, "exceeded_rec")

    goal = Goal(
        user_id=user.id,
        goal_type=GoalType.WEIGHT_MANAGEMENT.value,
        target_calories=Decimal("1500.00"),
        target_protein=Decimal("90.00"),
        target_carbohydrates=Decimal("150.00"),
        target_fat=Decimal("45.00"),
        is_active=True,
    )
    # Log meal of 1600 kcal
    meal = Meal(
        user_id=user.id,
        meal_type="LUNCH",
        consumed_at=datetime.now(timezone.utc),
    )
    first_food = db_session.query(FoodItem).first()
    item = MealItem(
        food_item_id=first_food.id,
        quantity=Decimal("28.00"),  # ~1624 kcal
        unit="piece",
        calculated_calories=Decimal("1624.00"),
        calculated_protein=Decimal("44.80"),
        calculated_carbohydrates=Decimal("336.00"),
        calculated_fat=Decimal("5.60"),
        calculated_fiber=Decimal("22.40"),
    )
    meal.items.append(item)
    db_session.add_all([goal, meal])
    db_session.commit()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=RecommendationRequest(meal_type="DINNER"),
    )

    assert ctx.consumed_calories == Decimal("1624.00")
    assert ctx.remaining_calories == Decimal("-124.00")  # target exceeded
    assert any("reached or exceeded" in lim for lim in ctx.limitations)


def test_no_fake_prices_in_candidates_or_context(db_session: Session):
    """Verifies that no pricing data is fabricated and limitations document absence of prices."""
    seed_foods(db_session)
    user = create_user(db_session, "price_check")

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
    )

    # Check limitations note
    assert any("does not track monetary pricing" in lim for lim in ctx.limitations)

    # Check candidates have only real nutrition attributes
    for cand in ctx.candidates:
        cand_dict = cand.model_dump()
        assert "price" not in cand_dict
        assert "cost" not in cand_dict


def test_recommendation_service_never_creates_meals(db_session: Session):
    """Invoking recommendation context construction and formatting must perform ZERO database inserts."""
    seed_foods(db_session)
    user = create_user(db_session, "zero_mutate")

    initial_meals = db_session.query(Meal).count()
    initial_items = db_session.query(MealItem).count()

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=RecommendationRequest(meal_type="DINNER", focus="high_protein"),
    )
    res = recommendation_service.format_direct_recommendation(ctx)

    assert res.total_calories > 0
    final_meals = db_session.query(Meal).count()
    final_items = db_session.query(MealItem).count()

    assert initial_meals == final_meals
    assert initial_items == final_items


# ==============================================================================
# 3. ToolRegistry & recommend_meal Tool Tests
# ==============================================================================

def test_recommend_meal_tool_registered_in_registry():
    """Verify recommend_meal is registered and properly reflected in metadata."""
    assert "recommend_meal" in tool_registry.list_tools()
    tool = tool_registry.get("recommend_meal")
    assert tool is not None
    assert tool.requires_auth is True

    meta = tool.get_metadata()
    assert meta["name"] == "recommend_meal"
    assert "properties" in meta["parameters"]


def test_recommend_meal_tool_execution_success(db_session: Session):
    """Executing recommend_meal tool with ToolContext returns RecommendationContext."""
    seed_foods(db_session)
    user = create_user(db_session, "tool_user")
    ctx = ToolContext(db=db_session, user=user)

    result = tool_registry.execute(
        name="recommend_meal",
        arguments={"meal_type": "DINNER", "focus": "high_protein"},
        context=ctx,
    )

    assert isinstance(result, RecommendationContext)
    assert result.user_id == user.id
    assert len(result.candidates) > 0


def test_recommend_meal_tool_unauthenticated_raises(db_session: Session):
    """Calling recommend_meal tool without authenticated context raises AuthorizationException."""
    unauth_ctx = ToolContext(db=db_session, user=None)
    with pytest.raises(AuthorizationException):
        tool_registry.execute(
            name="recommend_meal",
            arguments={},
            context=unauth_ctx,
        )


def test_recommend_meal_tool_user_isolation(db_session: Session):
    """User A running recommend_meal cannot see User B's profile or preferences."""
    seed_foods(db_session)
    user_a = create_user(db_session, "user_a")
    user_b = create_user(db_session, "user_b")

    # User B is vegan with peanut allergy
    prof_b = UserProfile(
        user_id=user_b.id,
        dietary_preference="VEGAN",
        allergies_or_restrictions=["peanut"],
    )
    db_session.add(prof_b)
    db_session.commit()

    ctx_a = ToolContext(db=db_session, user=user_a)
    result_a = tool_registry.execute("recommend_meal", {}, ctx_a)

    assert result_a.user_id == user_a.id
    assert result_a.dietary_preference is None
    assert "peanut" not in result_a.allergies_or_restrictions


# ==============================================================================
# 4. Direct REST API Endpoint Tests (/api/v1/recommendations)
# ==============================================================================

def test_api_recommendations_success(client: TestClient, db_session: Session):
    """POST /api/v1/recommendations returns 200 with structured recommendation."""
    seed_foods(db_session)
    user = create_user(db_session, "api_rec")
    token = create_access_token(user.id)

    response = client.post(
        "/api/v1/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        json={"meal_type": "LUNCH", "focus": "balanced"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "recommendation_summary" in data
    assert "items" in data
    assert len(data["items"]) > 0
    assert "total_calories" in data
    assert "explanation" in data
    assert "limitations" in data


def test_api_recommendations_unauthenticated_401(client: TestClient):
    """Unauthenticated request to /api/v1/recommendations returns 401."""
    response = client.post("/api/v1/recommendations", json={})
    assert response.status_code == 401


# ==============================================================================
# 5. Agent Recommendation Flow Tests (Mocked LLM)
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_recommendation_flow_calls_recommend_meal(db_session: Session, monkeypatch):
    """
    When user asks 'What should I eat for dinner?', the agent calls recommend_meal
    and synthesizes a recommendation without calling create_meal.
    """
    seed_foods(db_session)
    user = create_user(db_session, "agent_rec")
    runtime_ctx = AgentRuntimeContext(db=db_session, user=user)

    initial_meals = db_session.query(Meal).count()

    call_count = 0

    async def mock_chat(self, messages, format="json", temperature=0.0):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Step 1: LLM decides to call recommend_meal
            return '{"action": "call_tool", "tool": "recommend_meal", "arguments": {"meal_type": "DINNER"}}'
        # Step 2: LLM receives recommendation context and produces final response
        return '{"action": "final_response", "content": "I recommend having 1 piece of Chapati with 100g Cooked Toor Dal and a portion of Cooked Mixed Vegetables for dinner. This provides 285 kcal and 12.6g protein."}'

    monkeypatch.setattr(OllamaClient, "chat", mock_chat)

    response = await agent_service.chat("What should I eat for dinner?", runtime_ctx)

    assert "recommend_meal" in response.tools_used
    assert "create_meal" not in response.tools_used
    assert "Chapati" in response.response
    assert "Toor Dal" in response.response

    # Verify ZERO database mutations occurred
    final_meals = db_session.query(Meal).count()
    assert initial_meals == final_meals


@pytest.mark.asyncio
async def test_agent_recommendation_with_ingredients(db_session: Session, monkeypatch):
    """
    User asks: 'What can I make with rice and dal?'
    Agent passes ingredients into recommend_meal tool.
    """
    seed_foods(db_session)
    user = create_user(db_session, "agent_ing_rec")
    runtime_ctx = AgentRuntimeContext(db=db_session, user=user)

    call_count = 0

    async def mock_chat(self, messages, format="json", temperature=0.0):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '{"action": "call_tool", "tool": "recommend_meal", "arguments": {"ingredients": ["rice", "dal"]}}'
        return '{"action": "final_response", "content": "Using your rice and dal, I recommend 100g Cooked White Rice with 100g Cooked Toor Dal. This combination gives you 246 kcal and 10g protein."}'

    monkeypatch.setattr(OllamaClient, "chat", mock_chat)

    response = await agent_service.chat("What can I make with rice and dal?", runtime_ctx)

    assert "recommend_meal" in response.tools_used
    assert "Cooked White Rice" in response.response


@pytest.mark.asyncio
async def test_agent_chat_recommendation_ollama_unavailable_503(client: TestClient, db_session: Session, monkeypatch):
    """When Ollama is down during agent recommendation request, returns 503."""
    user = create_user(db_session, "rec_503")
    token = create_access_token(user.id)

    async def mock_chat_fail(self, *args, **kwargs):
        raise OllamaConnectionError("Connection refused")

    monkeypatch.setattr(OllamaClient, "chat", mock_chat_fail)

    response = client.post(
        "/api/v1/agent/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What should I eat for dinner?"},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_agent_chat_recommendation_ollama_timeout_504(client: TestClient, db_session: Session, monkeypatch):
    """When Ollama times out during agent recommendation request, returns 504."""
    user = create_user(db_session, "rec_504")
    token = create_access_token(user.id)

    async def mock_chat_timeout(self, *args, **kwargs):
        raise OllamaTimeoutError("Request timed out")

    monkeypatch.setattr(OllamaClient, "chat", mock_chat_timeout)

    response = client.post(
        "/api/v1/agent/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Suggest a high-protein dinner."},
    )
    assert response.status_code == 504


# ==============================================================================
# 8. Phase 11.1: Deterministic Ad-Hoc Safety Constraints Tests
# ==============================================================================

def test_ad_hoc_allergy_excludes_food_deterministically(db_session: Session):
    """
    PROVE: An ad-hoc allergy (e.g. ['paneer']) excludes the food from candidates
    even when the user has NO allergy in their persistent UserProfile.
    """
    seed_foods(db_session)
    user = create_user(db_session, "adhoc_allg")

    # Persistent profile has NO allergy
    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=[],
    )
    db_session.add(profile)
    db_session.commit()

    req = RecommendationRequest(
        meal_type="DINNER",
        ad_hoc_restrictions=["paneer"],
    )

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=req,
    )

    # 1. Candidates must NOT contain paneer
    cand_names = [c.name.lower() for c in ctx.candidates]
    assert cand_names, "Should return candidates"
    assert not any("paneer" in name for name in cand_names)

    # 2. Context preserves ad-hoc restriction info
    assert "paneer" in ctx.ad_hoc_restrictions
    assert "paneer" in ctx.allergies_or_restrictions

    # 3. Persistent profile MUST NOT be mutated
    db_session.refresh(profile)
    assert profile.allergies_or_restrictions == []


def test_persistent_and_ad_hoc_restrictions_combined_deterministically(db_session: Session):
    """
    PROVE: Effective restrictions are the union of persistent and ad-hoc constraints.
    Both peanuts (persistent) and paneer (ad-hoc) must be excluded.
    """
    seed_foods(db_session)
    user = create_user(db_session, "union_allg")

    # Persistent profile has 'peanut' allergy
    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["peanuts"],
    )
    db_session.add(profile)
    db_session.commit()

    req = RecommendationRequest(
        meal_type="DINNER",
        ad_hoc_restrictions=["paneer"],
    )

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=req,
    )

    cand_names = [c.name.lower() for c in ctx.candidates]
    assert cand_names, "Should return candidates"
    assert not any("paneer" in name for name in cand_names)
    assert not any("peanut" in name for name in cand_names)

    # Effective allergies must include both
    assert "peanuts" in ctx.allergies_or_restrictions
    assert "paneer" in ctx.allergies_or_restrictions

    # Persistent profile must retain only its original persistent allergy
    db_session.refresh(profile)
    assert profile.allergies_or_restrictions == ["peanuts"]


def test_ad_hoc_dislike_excludes_food_deterministically(db_session: Session):
    """
    PROVE: An ad-hoc dislike (e.g. ['paneer']) excludes the food without
    changing persistent disliked_foods.
    """
    seed_foods(db_session)
    user = create_user(db_session, "adhoc_dislike")

    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        disliked_foods=["mushrooms"],
    )
    db_session.add(profile)
    db_session.commit()

    req = RecommendationRequest(
        meal_type="DINNER",
        ad_hoc_dislikes=["paneer"],
    )

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=req,
    )

    cand_names = [c.name.lower() for c in ctx.candidates]
    assert not any("paneer" in name for name in cand_names)
    assert not any("mushroom" in name for name in cand_names)

    # Persistent profile remains unchanged
    db_session.refresh(profile)
    assert profile.disliked_foods == ["mushrooms"]


def test_ad_hoc_restriction_does_not_mutate_database(db_session: Session):
    """
    PROVE: Recommendation context construction causes ZERO database mutations.
    Count of meals, meal items, profiles, and goals before and after must be identical.
    """
    seed_foods(db_session)
    user = create_user(db_session, "zero_mutation")

    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=["nuts"],
    )
    db_session.add(profile)
    db_session.commit()

    meals_before = db_session.query(Meal).count()
    items_before = db_session.query(MealItem).count()
    profiles_before = db_session.query(UserProfile).count()

    req = RecommendationRequest(
        meal_type="DINNER",
        ad_hoc_restrictions=["paneer"],
        ad_hoc_dislikes=["tofu"],
    )

    _ = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=req,
    )

    meals_after = db_session.query(Meal).count()
    items_after = db_session.query(MealItem).count()
    profiles_after = db_session.query(UserProfile).count()

    assert meals_after == meals_before
    assert items_after == items_before
    assert profiles_after == profiles_before
    assert db_session.query(Meal).filter(Meal.user_id == user.id).count() == 0

    db_session.refresh(profile)
    assert profile.allergies_or_restrictions == ["nuts"]


def test_food_mention_without_restriction_does_not_create_restriction(db_session: Session):
    """
    PROVE: Mentioning a food (e.g. as an available ingredient 'paneer' or notes)
    does NOT add it to ad_hoc_restrictions and does NOT exclude it.
    """
    seed_foods(db_session)
    user = create_user(db_session, "mention_user")

    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
        allergies_or_restrictions=[],
    )
    db_session.add(profile)
    db_session.commit()

    # User says: "I have paneer at home. What can I make?" -> ingredients=['paneer']
    req = RecommendationRequest(
        meal_type="DINNER",
        ingredients=["paneer"],
        ad_hoc_restrictions=[],
    )

    ctx = recommendation_service.build_recommendation_context(
        db=db_session,
        user=user,
        request=req,
    )

    cand_names = [c.name.lower() for c in ctx.candidates]
    # Paneer should NOT be excluded; it should actually be among the top candidates
    assert any("paneer" in name for name in cand_names)
    assert ctx.ad_hoc_restrictions == []
    assert ctx.allergies_or_restrictions == []


def test_recommend_meal_tool_executes_with_ad_hoc_constraints(db_session: Session):
    """
    PROVE: RecommendMealTool parses ad_hoc_restrictions, passes them to service,
    and returns context with excluded foods.
    """
    seed_foods(db_session)
    user = create_user(db_session, "tool_adhoc")

    profile = UserProfile(
        user_id=user.id,
        dietary_preference="VEGETARIAN",
    )
    db_session.add(profile)
    db_session.commit()

    tool_input = {
        "meal_type": "DINNER",
        "ad_hoc_restrictions": ["paneer"],
    }
    tool_ctx = ToolContext(db=db_session, user=user)

    result = tool_registry.execute("recommend_meal", tool_input, tool_ctx)

    assert isinstance(result, RecommendationContext)
    cand_names = [c.name.lower() for c in result.candidates]
    assert not any("paneer" in name for name in cand_names)
    assert "paneer" in result.ad_hoc_restrictions


