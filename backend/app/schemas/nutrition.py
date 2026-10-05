"""
Pydantic schemas for daily and historical nutrition aggregation.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.meal import NutritionTotals


class MacroTargets(BaseModel):
    """Nutrition target goals."""
    calories: Optional[Decimal] = Field(None, description="Daily target calories (kcal)")
    protein: Optional[Decimal] = Field(None, description="Daily target protein (g)")
    carbohydrates: Optional[Decimal] = Field(None, description="Daily target carbohydrates (g)")
    fat: Optional[Decimal] = Field(None, description="Daily target fat (g)")


class DailyNutritionResponse(BaseModel):
    """Aggregated daily nutrition metrics, active target comparison, and remaining intake."""
    date: date
    meals_count: int = Field(default=0, description="Total meals logged for this calendar date")
    consumed: NutritionTotals
    target: Optional[MacroTargets] = Field(None, description="Active user goal targets, if configured")
    remaining: Optional[MacroTargets] = Field(None, description="Remaining nutritional allowance: max(target - consumed, 0)")


class NutritionHistoryResponse(BaseModel):
    """Historical daily nutrition records over a requested date range."""
    start_date: date
    end_date: date
    days: List[DailyNutritionResponse]
