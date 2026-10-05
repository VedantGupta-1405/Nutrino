"""
Pydantic schemas for FoodItem representation, queries, and nutrition calculation results.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FoodCategory(str, Enum):
    GRAIN = "GRAIN"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    DAIRY = "DAIRY"
    LEGUME = "LEGUME"
    MEAT = "MEAT"
    BEVERAGE = "BEVERAGE"
    SNACK = "SNACK"
    OTHER = "OTHER"


class FoodSource(str, Enum):
    INTERNAL_DEV_DATASET = "INTERNAL_DEV_DATASET"
    USDA = "USDA"
    USER_DEFINED = "USER_DEFINED"
    OTHER = "OTHER"


class FoodItemBase(BaseModel):
    """Base attributes for food item records."""

    name: str = Field(..., min_length=1, max_length=150, description="Normalized food name")
    description: Optional[str] = Field(None, max_length=500, description="Optional brief description")
    category: str = Field(default="OTHER", description="Food category for filtering")
    serving_size: Decimal = Field(..., gt=0, description="Base serving size quantity (must be positive)")
    serving_unit: str = Field(..., min_length=1, max_length=50, description="Base serving unit (e.g., gram, piece, ml)")
    calories: Decimal = Field(..., ge=0, description="Calories in kcal per base serving")
    protein: Decimal = Field(..., ge=0, description="Protein in grams per base serving")
    carbohydrates: Decimal = Field(..., ge=0, description="Carbohydrates in grams per base serving")
    fat: Decimal = Field(..., ge=0, description="Fat in grams per base serving")
    fiber: Decimal = Field(default=Decimal("0.00"), ge=0, description="Dietary fiber in grams per base serving")
    source: str = Field(default="INTERNAL_DEV_DATASET", description="Provenance of nutrition data")

    @field_validator("name", "serving_unit", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                raise ValueError("String field cannot be empty")
            return clean
        return v

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().upper()
            return val if val in FoodCategory.__members__ else "OTHER"
        return "OTHER"


class FoodItemCreate(FoodItemBase):
    """Schema for creating a food item."""
    pass


class FoodItemUpdate(BaseModel):
    """Schema for updating a food item."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    serving_size: Optional[Decimal] = Field(None, gt=0)
    serving_unit: Optional[str] = Field(None, min_length=1, max_length=50)
    calories: Optional[Decimal] = Field(None, ge=0)
    protein: Optional[Decimal] = Field(None, ge=0)
    carbohydrates: Optional[Decimal] = Field(None, ge=0)
    fat: Optional[Decimal] = Field(None, ge=0)
    fiber: Optional[Decimal] = Field(None, ge=0)
    source: Optional[str] = None


class FoodItemResponse(FoodItemBase):
    """Serialized food item output."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NutritionCalculationResult(BaseModel):
    """Result of deterministic nutrition calculation for a specified food quantity and unit."""
    food_id: int
    food_name: str
    quantity: Decimal
    unit: str
    serving_basis: str
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal
