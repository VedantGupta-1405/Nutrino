"""
Comprehensive unit and integration tests for Phase 7: Controlled Agent Tools.
Tests all 11 controlled tools, ToolRegistry, strict user isolation, authenticated context
enforcement, input validation, and boundary conditions.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.seed import seed_foods
from app.exceptions.base import (
    AuthorizationException,
    ResourceNotFoundException,
    ValidationException,
)
from app.models.goal import Goal
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.goal import GoalType
from app.schemas.profile import ActivityLevel, DietaryPreference
from app.schemas.meal import MealItemCreate, MealType
from app.auth.security import get_password_hash
from app.services.food_service import food_service
from app.services.goal_service import goal_service
from app.services.profile_service import profile_service
from app.tools import (
    CreateMealInput,
    CreateMealTool,
    DeleteMealInput,
    DeleteMealTool,
    EmptyInput,
    GetActiveGoalTool,
    GetFoodInput,
    GetFoodTool,
    GetMealInput,
    GetMealTool,
    GetNutritionForDateInput,
    GetNutritionHistoryInput,
    GetNutritionHistoryTool,
    GetNutritionTool,
    GetTodayMealsTool,
    GetTodayNutritionTool,
    GetUserProfileTool,
    SearchFoodsInput,
    SearchFoodTool,
    ToolContext,
    ToolRegistry,
    create_default_registry,
    tool_registry,
)


def create_test_user(db: Session, prefix: str = "tooluser", is_active: bool = True) -> User:
    """Helper to persist an active User entity directly in the test database."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        name="Tool Test User",
        email=email,
        password_hash=get_password_hash("SecretPassword123!"),
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==============================================================================
# 1. TOOL REGISTRY TESTS
# ==============================================================================

def test_registry_contains_all_eleven_tools():
    """Verify registry has exactly the 11 expected controlled tools."""
    expected_tools = {
        "search_foods",
        "get_food",
        "get_user_profile",
        "get_active_goal",
        "create_meal",
        "get_today_meals",
        "get_meal",
        "delete_meal",
        "get_today_nutrition",
        "get_nutrition",
        "get_nutrition_history",
    }
    registered = set(tool_registry.list_tools())
    assert expected_tools == registered
    assert len(registered) == 11


def test_registry_get_metadata_schemas():
    """Verify metadata generation produces valid schema representations for agent orchestration."""
    metadata = tool_registry.get_tool_metadata()
    assert len(metadata) == 11
    for meta in metadata:
        assert "name" in meta
        assert "description" in meta
        assert "parameters" in meta
        assert "properties" in meta["parameters"]
        assert "requires_auth" in meta


def test_registry_unknown_tool_raises_resource_not_found(db_session: Session):
    """Executing an unregistered tool must raise ResourceNotFoundException."""
    user = create_test_user(db_session)
    context = ToolContext(db=db_session, user=user)
    with pytest.raises(ResourceNotFoundException) as exc_info:
        tool_registry.execute("execute_arbitrary_code", {}, context)
    assert exc_info.value.details["resource"] == "Tool"
    assert exc_info.value.details["identifier"] == "execute_arbitrary_code"


def test_registry_duplicate_registration_raises_validation_exception():
    """Registering duplicate tool names must be rejected."""
    custom_reg = ToolRegistry()
    custom_reg.register(SearchFoodTool())
    with pytest.raises(ValidationException) as exc_info:
        custom_reg.register(SearchFoodTool())
    assert "already registered" in str(exc_info.value)


# ==============================================================================
# 2. FOOD TOOLS TESTS
# ==============================================================================

def test_search_food_tool_success(db_session: Session):
    """Test search_foods returns matching items with correct summaries."""
    seed_foods(db_session)
    context = ToolContext(db=db_session)
    tool = SearchFoodTool()

    # Search by keyword
    output = tool.execute(SearchFoodsInput(query="Idli"), context)
    assert output.count >= 1
    found = [f for f in output.foods if f.name == "Idli"]
    assert len(found) == 1
    assert found[0].category == "GRAIN"
    assert found[0].serving_unit == "piece"


def test_search_food_tool_category_filter_and_empty(db_session: Session):
    """Test category filtering and empty results."""
    seed_foods(db_session)
    context = ToolContext(db=db_session)
    tool = SearchFoodTool()

    # Filter with category
    output = tool.execute(SearchFoodsInput(query="Apple", category="GRAINS"), context)
    assert output.count == 0

    # Non-existent query
    output2 = tool.execute(SearchFoodsInput(query="NonExistentFoodXYZ"), context)
    assert output2.count == 0
    assert len(output2.foods) == 0


def test_get_food_tool_success(db_session: Session):
    """Test retrieving food item details by catalog ID."""
    seed_foods(db_session)
    idli = food_service.get_by_name(db_session, "Idli")
    assert idli is not None

    context = ToolContext(db=db_session)
    tool = GetFoodTool()
    food = tool.execute(GetFoodInput(food_id=idli.id), context)

    assert food.id == idli.id
    assert food.name == "Idli"
    assert food.calories == idli.calories
    assert food.protein == idli.protein


def test_get_food_tool_not_found(db_session: Session):
    """Test get_food raises ResourceNotFoundException for unknown ID."""
    context = ToolContext(db=db_session)
    tool = GetFoodTool()
    with pytest.raises(ResourceNotFoundException) as exc_info:
        tool.execute(GetFoodInput(food_id=999999), context)
    assert exc_info.value.details["resource"] == "FoodItem"


# ==============================================================================
# 3. PROFILE TOOLS TESTS
# ==============================================================================

def test_get_user_profile_tool_success(db_session: Session):
    """Test retrieving authenticated user's profile."""
    user = create_test_user(db_session, "prof_succ")
    profile = UserProfile(
        user_id=user.id,
        age=28,
        height=175.0,
        weight=72.5,
        activity_level="MODERATELY_ACTIVE",
        dietary_preference="VEGETARIAN",
        preferred_cuisine=["Indian"],
        allergies_or_restrictions=["peanuts"],
        disliked_foods=["mushrooms"],
        budget_per_day=400.00,
        available_ingredients=["paneer", "rice"],
    )
    db_session.add(profile)
    db_session.commit()

    context = ToolContext(db=db_session, user=user)
    tool = GetUserProfileTool()
    result = tool.execute(EmptyInput(), context)

    assert result.user_id == user.id
    assert result.age == 28
    assert result.dietary_preference == DietaryPreference.VEGETARIAN
    assert "peanuts" in result.allergies_or_restrictions


def test_get_user_profile_tool_not_found(db_session: Session):
    """Test profile tool raises ResourceNotFoundException if profile not set."""
    user = create_test_user(db_session, "noprof")
    context = ToolContext(db=db_session, user=user)
    tool = GetUserProfileTool()
    with pytest.raises(ResourceNotFoundException) as exc_info:
        tool.execute(EmptyInput(), context)
    assert exc_info.value.details["resource"] == "UserProfile"


def test_get_user_profile_tool_isolation(db_session: Session):
    """Verify User A's context cannot view User B's profile."""
    user_a = create_test_user(db_session, "user_a")
    user_b = create_test_user(db_session, "user_b")

    profile_b = UserProfile(
        user_id=user_b.id,
        age=35,
        height=180.0,
        weight=85.0,
        activity_level="VERY_ACTIVE",
        dietary_preference="VEGAN",
    )
    db_session.add(profile_b)
    db_session.commit()

    # User A has no profile
    context_a = ToolContext(db=db_session, user=user_a)
    tool = GetUserProfileTool()
    with pytest.raises(ResourceNotFoundException):
        tool.execute(EmptyInput(), context_a)


# ==============================================================================
# 4. GOAL TOOLS TESTS
# ==============================================================================

def test_get_active_goal_tool_success(db_session: Session):
    """Test retrieving authenticated user's active goal."""
    user = create_test_user(db_session, "goal_succ")
    goal = Goal(
        user_id=user.id,
        goal_type=GoalType.MUSCLE_GAIN,
        target_calories=Decimal("2600.00"),
        target_protein=Decimal("150.00"),
        target_carbohydrates=Decimal("300.00"),
        target_fat=Decimal("70.00"),
        is_active=True,
    )
    db_session.add(goal)
    db_session.commit()

    context = ToolContext(db=db_session, user=user)
    tool = GetActiveGoalTool()
    result = tool.execute(EmptyInput(), context)

    assert result.user_id == user.id
    assert result.goal_type == GoalType.MUSCLE_GAIN
    assert result.target_calories == Decimal("2600.00")
    assert result.target_protein == Decimal("150.00")


def test_get_active_goal_tool_not_found(db_session: Session):
    """Test goal tool raises ResourceNotFoundException if no active goal exists."""
    user = create_test_user(db_session, "nogoal")
    context = ToolContext(db=db_session, user=user)
    tool = GetActiveGoalTool()
    with pytest.raises(ResourceNotFoundException) as exc_info:
        tool.execute(EmptyInput(), context)
    assert exc_info.value.details["resource"] == "Goal"


# ==============================================================================
# 5. MEAL TOOLS TESTS
# ==============================================================================

def test_create_meal_tool_single_and_multiple_items(db_session: Session):
    """Test creating meals via CreateMealTool with single and multiple items."""
    seed_foods(db_session)
    user = create_test_user(db_session, "createmeal")
    context = ToolContext(db=db_session, user=user)

    idli = food_service.get_by_name(db_session, "Idli")
    rice = food_service.get_by_name(db_session, "Cooked White Rice")
    assert idli is not None
    assert rice is not None

    tool = CreateMealTool()

    # Single item meal
    single_input = CreateMealInput(
        meal_type=MealType.BREAKFAST,
        items=[MealItemCreate(food_id=idli.id, quantity=Decimal("3.0"), unit="piece")],
    )
    res1 = tool.execute(single_input, context)
    assert res1.user_id == user.id
    assert res1.meal_type == MealType.BREAKFAST
    assert len(res1.items) == 1
    # 58 kcal * 3 = 174 kcal
    assert res1.totals.calories == Decimal("174.00")

    # Multi item meal
    multi_input = CreateMealInput(
        meal_type=MealType.LUNCH,
        items=[
            MealItemCreate(food_id=idli.id, quantity=Decimal("2.0"), unit="piece"),
            MealItemCreate(food_id=rice.id, quantity=Decimal("150.0"), unit="gram"),
        ],
    )
    res2 = tool.execute(multi_input, context)
    assert res2.user_id == user.id
    assert res2.meal_type == MealType.LUNCH
    assert len(res2.items) == 2


def test_create_meal_tool_invalid_food_raises_not_found(db_session: Session):
    """Creating a meal with non-existent food ID raises ResourceNotFoundException."""
    user = create_test_user(db_session, "badfood")
    context = ToolContext(db=db_session, user=user)
    tool = CreateMealTool()

    bad_input = CreateMealInput(
        meal_type=MealType.DINNER,
        items=[MealItemCreate(food_id=999999, quantity=Decimal("1.0"), unit="piece")],
    )
    with pytest.raises(ResourceNotFoundException):
        tool.execute(bad_input, context)


def test_get_today_meals_tool(db_session: Session):
    """Test get_today_meals returns meals logged today for authenticated user."""
    seed_foods(db_session)
    user = create_test_user(db_session, "todaymeals")
    context = ToolContext(db=db_session, user=user)
    idli = food_service.get_by_name(db_session, "Idli")

    create_tool = CreateMealTool()
    get_today_tool = GetTodayMealsTool()

    # Before logging
    init_res = get_today_tool.execute(EmptyInput(), context)
    assert init_res.count == 0

    # Log 2 meals today
    create_tool.execute(
        CreateMealInput(
            meal_type=MealType.BREAKFAST,
            items=[MealItemCreate(food_id=idli.id, quantity=Decimal("2.0"), unit="piece")],
        ),
        context,
    )
    create_tool.execute(
        CreateMealInput(
            meal_type=MealType.SNACK,
            items=[MealItemCreate(food_id=idli.id, quantity=Decimal("1.0"), unit="piece")],
        ),
        context,
    )

    today_res = get_today_tool.execute(EmptyInput(), context)
    assert today_res.count == 2
    assert len(today_res.meals) == 2


def test_get_meal_tool_success_and_unauthorized_isolation(db_session: Session):
    """Test get_meal returns meal for owner, but raises ResourceNotFoundException for another user."""
    seed_foods(db_session)
    user_a = create_test_user(db_session, "meala")
    user_b = create_test_user(db_session, "mealb")
    idli = food_service.get_by_name(db_session, "Idli")

    context_a = ToolContext(db=db_session, user=user_a)
    context_b = ToolContext(db=db_session, user=user_b)

    create_tool = CreateMealTool()
    meal_a = create_tool.execute(
        CreateMealInput(
            meal_type=MealType.LUNCH,
            items=[MealItemCreate(food_id=idli.id, quantity=Decimal("2.0"), unit="piece")],
        ),
        context_a,
    )

    get_tool = GetMealTool()

    # User A accesses own meal -> Success
    res = get_tool.execute(GetMealInput(meal_id=meal_a.id), context_a)
    assert res.id == meal_a.id
    assert res.user_id == user_a.id

    # User B attempts to access User A's meal -> ResourceNotFoundException (ownership isolation)
    with pytest.raises(ResourceNotFoundException):
        get_tool.execute(GetMealInput(meal_id=meal_a.id), context_b)


def test_delete_meal_tool_success_and_isolation(db_session: Session):
    """Test delete_meal allows owner to delete, but blocks non-owner."""
    seed_foods(db_session)
    user_a = create_test_user(db_session, "dela")
    user_b = create_test_user(db_session, "delb")
    idli = food_service.get_by_name(db_session, "Idli")

    context_a = ToolContext(db=db_session, user=user_a)
    context_b = ToolContext(db=db_session, user=user_b)

    create_tool = CreateMealTool()
    meal_a = create_tool.execute(
        CreateMealInput(
            meal_type=MealType.DINNER,
            items=[MealItemCreate(food_id=idli.id, quantity=Decimal("1.0"), unit="piece")],
        ),
        context_a,
    )

    delete_tool = DeleteMealTool()

    # User B attempts to delete User A's meal -> ResourceNotFoundException
    with pytest.raises(ResourceNotFoundException):
        delete_tool.execute(DeleteMealInput(meal_id=meal_a.id), context_b)

    # User A deletes own meal -> Success
    del_res = delete_tool.execute(DeleteMealInput(meal_id=meal_a.id), context_a)
    assert del_res.success is True
    assert del_res.meal_id == meal_a.id

    # Trying to delete already deleted meal -> ResourceNotFoundException
    with pytest.raises(ResourceNotFoundException):
        delete_tool.execute(DeleteMealInput(meal_id=meal_a.id), context_a)


# ==============================================================================
# 6. NUTRITION TOOLS TESTS
# ==============================================================================

def test_get_today_nutrition_tool(db_session: Session):
    """Test get_today_nutrition returns aggregated totals and goal comparisons."""
    seed_foods(db_session)
    user = create_test_user(db_session, "nutr_today")
    context = ToolContext(db=db_session, user=user)
    idli = food_service.get_by_name(db_session, "Idli")

    # Set active goal: 2000 kcal, 100g protein
    goal = Goal(
        user_id=user.id,
        goal_type=GoalType.WEIGHT_MANAGEMENT.value,
        target_calories=Decimal("2000.00"),
        target_protein=Decimal("100.00"),
        target_carbohydrates=Decimal("250.00"),
        target_fat=Decimal("60.00"),
        is_active=True,
    )
    db_session.add(goal)
    db_session.commit()

    # Log meal: 2 idlis = 116 kcal, 3.2g protein
    create_tool = CreateMealTool()
    create_tool.execute(
        CreateMealInput(
            meal_type=MealType.BREAKFAST,
            items=[MealItemCreate(food_id=idli.id, quantity=Decimal("2.0"), unit="piece")],
        ),
        context,
    )

    nutr_tool = GetTodayNutritionTool()
    result = nutr_tool.execute(EmptyInput(), context)

    assert result.meals_count == 1
    assert result.consumed.calories == Decimal("116.00")
    assert result.consumed.protein == Decimal("3.20")
    assert result.target.calories == Decimal("2000.00")
    assert result.remaining.calories == Decimal("1884.00")
    assert result.remaining.protein == Decimal("96.80")


def test_get_nutrition_tool_for_specific_date(db_session: Session):
    """Test get_nutrition for specific calendar date."""
    user = create_test_user(db_session, "nutr_date")
    context = ToolContext(db=db_session, user=user)
    tool = GetNutritionTool()

    target = date(2026, 1, 15)
    res = tool.execute(GetNutritionForDateInput(date=target), context)

    assert res.date == target
    assert res.meals_count == 0
    assert res.consumed.calories == Decimal("0.00")


def test_get_nutrition_history_tool_and_range_validation(db_session: Session):
    """Test get_nutrition_history across date ranges and enforces 31-day limit."""
    user = create_test_user(db_session, "nutr_hist")
    context = ToolContext(db=db_session, user=user)
    tool = GetNutritionHistoryTool()

    # Valid 7-day range
    start = date(2026, 1, 1)
    end = date(2026, 1, 7)
    res = tool.execute(GetNutritionHistoryInput(start_date=start, end_date=end), context)
    assert res.start_date == start
    assert res.end_date == end
    assert len(res.days) == 7

    # Invalid range: end before start
    with pytest.raises(ValidationException) as exc1:
        tool.execute(GetNutritionHistoryInput(start_date=date(2026, 1, 10), end_date=date(2026, 1, 5)), context)
    assert "start_date" in str(exc1.value)

    # Invalid range: > 31 days
    with pytest.raises(ValidationException) as exc2:
        tool.execute(
            GetNutritionHistoryInput(start_date=date(2026, 1, 1), end_date=date(2026, 2, 5)),
            context,
        )
    assert "31 days" in str(exc2.value)


# ==============================================================================
# 7. SECURITY & AUTHENTICATION ENFORCEMENT TESTS
# ==============================================================================

def test_unauthenticated_context_raises_authorization_exception(db_session: Session):
    """Tools with requires_auth=True must raise AuthorizationException when unauthenticated."""
    unauth_context = ToolContext(db=db_session, user=None)

    auth_required_tools = [
        GetUserProfileTool(),
        GetActiveGoalTool(),
        CreateMealTool(),
        GetTodayMealsTool(),
        GetMealTool(),
        DeleteMealTool(),
        GetTodayNutritionTool(),
        GetNutritionTool(),
        GetNutritionHistoryTool(),
    ]

    for tool in auth_required_tools:
        with pytest.raises(AuthorizationException):
            tool.run({}, unauth_context)


def test_inactive_user_raises_authorization_exception(db_session: Session):
    """An inactive user context must not be allowed to execute tools."""
    inactive_user = create_test_user(db_session, "inactive", is_active=False)
    inactive_context = ToolContext(db=db_session, user=inactive_user)

    tool = GetTodayNutritionTool()
    with pytest.raises(AuthorizationException) as exc_info:
        tool.execute(EmptyInput(), inactive_context)
    assert "active" in str(exc_info.value)


def test_llm_cannot_override_user_id_in_inputs(db_session: Session):
    """
    Ensure input schemas do NOT accept user_id.
    Even if an LLM sends a user_id key in dictionary arguments,
    it cannot hijack another user's execution context.
    """
    seed_foods(db_session)
    user_victim = create_test_user(db_session, "victim")
    user_attacker = create_test_user(db_session, "attacker")

    idli = food_service.get_by_name(db_session, "Idli")
    attacker_context = ToolContext(db=db_session, user=user_attacker)

    # Attacker passes victim's user_id in raw arguments to create_meal
    args = {
        "meal_type": "BREAKFAST",
        "items": [{"food_id": idli.id, "quantity": 1, "unit": "piece"}],
        "user_id": user_victim.id,  # Attempted spoof
    }

    meal_tool = CreateMealTool()
    result = meal_tool.run(args, attacker_context)

    # Created meal MUST belong to attacker, never to victim
    assert result.user_id == user_attacker.id
    assert result.user_id != user_victim.id


def test_registry_dispatch_flow(db_session: Session):
    """Verify executing a tool through tool_registry.execute works end-to-end."""
    seed_foods(db_session)
    context = ToolContext(db=db_session)

    res = tool_registry.execute("search_foods", {"query": "Rice"}, context)
    assert res.count >= 1
    assert any("Rice" in f.name for f in res.foods)
