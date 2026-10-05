"""
Pydantic schemas for Meal logging, validation, and serialized meal responses.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MealType(str, Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"
    OTHER = "OTHER"


SUPPORTED_MEAL_TYPES = {mt.value for mt in MealType}


class NutritionTotals(BaseModel):
    """Aggregated nutritional totals for a meal or day."""
    calories: Decimal = Field(default=Decimal("0.00"), description="Total energy in kcal")
    protein: Decimal = Field(default=Decimal("0.00"), description="Total protein in grams")
    carbohydrates: Decimal = Field(default=Decimal("0.00"), description="Total carbohydrates in grams")
    fat: Decimal = Field(default=Decimal("0.00"), description="Total fat in grams")
    fiber: Decimal = Field(default=Decimal("0.00"), description="Total dietary fiber in grams")


class MealItemCreate(BaseModel):
    """Schema for individual food item inside a meal creation request."""
    food_id: int = Field(..., gt=0, description="Database ID of the FoodItem")
    quantity: Decimal = Field(..., gt=0, le=10000, description="Quantity of food consumed (must be positive)")
    unit: str = Field(..., min_length=1, max_length=50, description="Serving unit (e.g. piece, gram, ml, cup)")

    @field_validator("unit", mode="before")
    @classmethod
    def sanitize_unit(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                raise ValueError("Unit cannot be empty")
            return clean
        return v


class MealCreate(BaseModel):
    """Schema for logging a complete meal."""
    meal_type: str = Field(..., description="Meal occasion: BREAKFAST, LUNCH, DINNER, SNACK, or OTHER")
    consumed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of meal consumption (ISO-8601). Defaults to current UTC time if not provided.",
    )
    items: List[MealItemCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of foods consumed in this meal (1-50 items)",
    )

    @field_validator("meal_type", mode="before")
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().upper()
            if val not in SUPPORTED_MEAL_TYPES:
                supported = ", ".join(sorted(SUPPORTED_MEAL_TYPES))
                raise ValueError(f"Invalid meal_type '{v}'. Must be one of: {supported}")
            return val
        raise ValueError("meal_type must be a string")

    @field_validator("consumed_at", mode="before")
    @classmethod
    def default_consumed_at(cls, v: Optional[datetime]) -> datetime:
        if v is None:
            return datetime.now(timezone.utc)
        return v


class MealItemResponse(BaseModel):
    """Serialized meal item output including calculated historical snapshot."""
    id: int
    food_item_id: int
    food_name: str
    quantity: Decimal
    unit: str
    calculated_calories: Decimal
    calculated_protein: Decimal
    calculated_carbohydrates: Decimal
    calculated_fat: Decimal
    calculated_fiber: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealResponse(BaseModel):
    """Serialized meal response with all item details and aggregated totals."""
    id: int
    user_id: int
    meal_type: str
    consumed_at: datetime
    items: List[MealItemResponse]
    totals: NutritionTotals
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
