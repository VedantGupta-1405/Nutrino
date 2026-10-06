"""
Controlled meal management tools for the agent layer.
Enforces user ownership, atomic transaction execution, and deterministic nutrition snapshots.
Calculations are performed strictly via NutritionCalculator in MealService.
"""

from datetime import datetime, timezone
from app.exceptions.base import ResourceNotFoundException
from app.schemas.meal import MealCreate, MealResponse
from app.services.meal_service import meal_service
from app.tools.base import BaseTool, EmptyInput, ToolContext
from app.tools.schemas import (
    CreateMealInput,
    DeleteMealInput,
    DeleteMealOutput,
    GetMealInput,
    MealListResponse,
)


class CreateMealTool(BaseTool[CreateMealInput, MealResponse]):
    """Tool for logging a user meal with structured food items."""

    name = "create_meal"
    description = (
        "Log a meal for the authenticated user by specifying meal type (BREAKFAST, LUNCH, "
        "DINNER, SNACK, OTHER), consumed items with catalog food IDs, quantities, and units. "
        "Calculates and persists deterministic nutrition snapshots automatically."
    )
    input_schema = CreateMealInput
    output_schema = MealResponse
    requires_auth = True

    def execute(self, params: CreateMealInput, context: ToolContext) -> MealResponse:
        user_id = context.user_id
        meal_in = MealCreate(
            meal_type=params.meal_type,
            items=params.items,
            consumed_at=params.consumed_at,
        )
        return meal_service.create_meal(
            db=context.db,
            user_id=user_id,
            meal_in=meal_in,
        )


class GetTodayMealsTool(BaseTool[EmptyInput, MealListResponse]):
    """Tool for retrieving all meals logged by the user today (UTC)."""

    name = "get_today_meals"
    description = (
        "Retrieve all meals logged by the authenticated user for today (UTC calendar date), "
        "including all consumed items, serving sizes, and calculated macronutrient totals."
    )
    input_schema = EmptyInput
    output_schema = MealListResponse
    requires_auth = True

    def execute(self, params: EmptyInput, context: ToolContext) -> MealListResponse:
        user_id = context.user_id
        today_utc = datetime.now(timezone.utc).date()
        meals = meal_service.get_meals_for_date(
            db=context.db,
            user_id=user_id,
            target_date=today_utc,
        )
        formatted_meals = [meal_service.format_meal_response(m) for m in meals]
        return MealListResponse(meals=formatted_meals, count=len(formatted_meals))


class GetMealTool(BaseTool[GetMealInput, MealResponse]):
    """Tool for retrieving a specific meal by ID."""

    name = "get_meal"
    description = (
        "Retrieve a specific meal by its ID for the authenticated user, "
        "including individual items and computed nutritional totals."
    )
    input_schema = GetMealInput
    output_schema = MealResponse
    requires_auth = True

    def execute(self, params: GetMealInput, context: ToolContext) -> MealResponse:
        user_id = context.user_id
        meal = meal_service.get_by_id(
            db=context.db,
            user_id=user_id,
            meal_id=params.meal_id,
        )
        if meal is None:
            raise ResourceNotFoundException("Meal", params.meal_id)
        return meal_service.format_meal_response(meal)


class DeleteMealTool(BaseTool[DeleteMealInput, DeleteMealOutput]):
    """Tool for deleting a specific meal owned by the user."""

    name = "delete_meal"
    description = (
        "Delete an existing meal record belonging to the authenticated user by its ID."
    )
    input_schema = DeleteMealInput
    output_schema = DeleteMealOutput
    requires_auth = True

    def execute(self, params: DeleteMealInput, context: ToolContext) -> DeleteMealOutput:
        user_id = context.user_id
        deleted = meal_service.delete_meal(
            db=context.db,
            user_id=user_id,
            meal_id=params.meal_id,
        )
        if not deleted:
            raise ResourceNotFoundException("Meal", params.meal_id)
        return DeleteMealOutput(
            success=True,
            meal_id=params.meal_id,
            message="Meal successfully deleted.",
        )
