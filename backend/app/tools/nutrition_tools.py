"""
Controlled nutrition aggregation tools for the agent layer.
Retrieves deterministic daily aggregates, macro targets, and historical trends.
Calculations and comparisons are performed strictly by the existing NutritionService.
"""

from datetime import datetime, timezone
from app.schemas.nutrition import (
    DailyNutritionResponse,
    NutritionHistoryResponse,
)
from app.services.nutrition_service import nutrition_service
from app.tools.base import BaseTool, EmptyInput, ToolContext
from app.tools.schemas import (
    GetNutritionForDateInput,
    GetNutritionHistoryInput,
)


class GetTodayNutritionTool(BaseTool[EmptyInput, DailyNutritionResponse]):
    """Tool for retrieving aggregated nutrition for today (UTC)."""

    name = "get_today_nutrition"
    description = (
        "Retrieve aggregated nutritional intake (total calories, protein, carbs, fat, fiber), "
        "active target comparison, and remaining allowance for the authenticated user for today."
    )
    input_schema = EmptyInput
    output_schema = DailyNutritionResponse
    requires_auth = True

    def execute(self, params: EmptyInput, context: ToolContext) -> DailyNutritionResponse:
        user_id = context.user_id
        today_utc = datetime.now(timezone.utc).date()
        return nutrition_service.get_daily_nutrition(
            db=context.db,
            user_id=user_id,
            target_date=today_utc,
        )


class GetNutritionTool(BaseTool[GetNutritionForDateInput, DailyNutritionResponse]):
    """Tool for retrieving aggregated nutrition on a specific date."""

    name = "get_nutrition"
    description = (
        "Retrieve aggregated nutritional intake, targets, and remaining allowance "
        "for the authenticated user on a specified calendar date (YYYY-MM-DD)."
    )
    input_schema = GetNutritionForDateInput
    output_schema = DailyNutritionResponse
    requires_auth = True

    def execute(self, params: GetNutritionForDateInput, context: ToolContext) -> DailyNutritionResponse:
        user_id = context.user_id
        return nutrition_service.get_daily_nutrition(
            db=context.db,
            user_id=user_id,
            target_date=params.date,
        )


class GetNutritionHistoryTool(BaseTool[GetNutritionHistoryInput, NutritionHistoryResponse]):
    """Tool for retrieving daily nutrition history across a date range."""

    name = "get_nutrition_history"
    description = (
        "Retrieve daily aggregated nutritional history for the authenticated user across "
        "a specified date range (maximum 31 days allowed)."
    )
    input_schema = GetNutritionHistoryInput
    output_schema = NutritionHistoryResponse
    requires_auth = True

    def execute(self, params: GetNutritionHistoryInput, context: ToolContext) -> NutritionHistoryResponse:
        user_id = context.user_id
        return nutrition_service.get_history(
            db=context.db,
            user_id=user_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
