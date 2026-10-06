"""
Pydantic schemas for controlled tool inputs and outputs.
Enforces type safety and input boundaries for all agent tool invocations.
"""

import datetime as dt
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.meal import MealType, MealItemCreate, MealResponse


class FoodSummaryItem(BaseModel):
    """Concise representation of a food catalog item for search discovery."""
    id: int = Field(..., description="Unique food item catalog ID")
    name: str = Field(..., description="Food item name")
    category: str = Field(..., description="Category (GRAINS, PROTEIN, etc.)")
    serving_size: Decimal = Field(..., description="Base serving quantity")
    serving_unit: str = Field(..., description="Base serving unit (e.g. piece, gram, cup)")
    source: str = Field(..., description="Catalog source dataset")


class SearchFoodsInput(BaseModel):
    """Input parameters for searching the food catalog."""
    query: str = Field(..., min_length=1, max_length=100, description="Food name or query string")
    category: Optional[str] = Field(default=None, description="Optional category filter")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of items to return")


class SearchFoodsOutput(BaseModel):
    """Output for food catalog search."""
    foods: List[FoodSummaryItem] = Field(default_factory=list, description="Matching food items")
    count: int = Field(..., description="Number of results returned")


class GetFoodInput(BaseModel):
    """Input parameter for retrieving a food item by ID."""
    food_id: int = Field(..., ge=1, description="Catalog ID of the food item")


class CreateMealInput(BaseModel):
    """
    Input schema for logging a meal.
    Accepts food IDs, quantities, and units.
    Must NOT contain calories or macronutrients (these are calculated deterministically by backend).
    """
    meal_type: MealType = Field(..., description="Meal category (BREAKFAST, LUNCH, DINNER, SNACK, OTHER)")
    items: List[MealItemCreate] = Field(..., min_length=1, max_length=50, description="Items consumed in the meal")
    consumed_at: Optional[dt.datetime] = Field(default=None, description="Optional consumption timestamp in UTC (defaults to current time)")


class GetMealInput(BaseModel):
    """Input parameter for retrieving a specific meal."""
    meal_id: int = Field(..., ge=1, description="ID of the meal to retrieve")


class DeleteMealInput(BaseModel):
    """Input parameter for deleting a specific meal."""
    meal_id: int = Field(..., ge=1, description="ID of the meal to delete")


class DeleteMealOutput(BaseModel):
    """Result of meal deletion."""
    success: bool = True
    meal_id: int = Field(..., description="ID of the deleted meal")
    message: str = Field(..., description="Status message")


class MealListResponse(BaseModel):
    """List of meals returned by query tools."""
    meals: List[MealResponse] = Field(default_factory=list, description="List of meals")
    count: int = Field(..., description="Number of meals")


class GetNutritionForDateInput(BaseModel):
    """Input parameter for retrieving nutrition on a specific date."""
    date: dt.date = Field(..., description="Target date in YYYY-MM-DD format")


class GetNutritionHistoryInput(BaseModel):
    """Input parameter for retrieving historical nutrition aggregation."""
    start_date: dt.date = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: dt.date = Field(..., description="End date in YYYY-MM-DD format")
