"""
Controlled Agent Tools package for Nutrino.
Provides deterministic, authenticated interfaces for the future AI agent layer.
"""

from app.tools.base import BaseTool, EmptyInput, ToolContext, ToolResult
from app.tools.food_tools import GetFoodTool, SearchFoodTool
from app.tools.goal_tools import GetActiveGoalTool
from app.tools.meal_tools import (
    CreateMealTool,
    DeleteMealTool,
    GetMealTool,
    GetTodayMealsTool,
)
from app.tools.nutrition_tools import (
    GetNutritionHistoryTool,
    GetNutritionTool,
    GetTodayNutritionTool,
)
from app.tools.profile_tools import GetUserProfileTool
from app.tools.recommend_tools import RecommendMealTool
from app.tools.registry import ToolRegistry, create_default_registry, tool_registry
from app.tools.schemas import (
    CreateMealInput,
    DeleteMealInput,
    DeleteMealOutput,
    FoodSummaryItem,
    GetFoodInput,
    GetMealInput,
    GetNutritionForDateInput,
    GetNutritionHistoryInput,
    MealListResponse,
    RecommendMealInput,
    SearchFoodsInput,
    SearchFoodsOutput,
)

__all__ = [
    "BaseTool",
    "EmptyInput",
    "ToolContext",
    "ToolResult",
    "SearchFoodTool",
    "GetFoodTool",
    "GetUserProfileTool",
    "GetActiveGoalTool",
    "CreateMealTool",
    "GetTodayMealsTool",
    "GetMealTool",
    "DeleteMealTool",
    "GetTodayNutritionTool",
    "GetNutritionTool",
    "GetNutritionHistoryTool",
    "ToolRegistry",
    "create_default_registry",
    "tool_registry",
    "FoodSummaryItem",
    "SearchFoodsInput",
    "SearchFoodsOutput",
    "GetFoodInput",
    "CreateMealInput",
    "GetMealInput",
    "DeleteMealInput",
    "DeleteMealOutput",
    "MealListResponse",
    "GetNutritionForDateInput",
    "GetNutritionHistoryInput",
    "RecommendMealTool",
    "RecommendMealInput",
]
