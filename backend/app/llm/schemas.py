"""
Pydantic schemas for LLM structured output and meal extraction.
These schemas strictly represent natural-language entity extraction and do NOT include
authoritative nutrition calculations or database IDs.
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.meal import MealType


class ExtractedMealItem(BaseModel):
    """
    A single food item extracted from natural language input.
    If the user did not specify quantity or unit, they remain None to preserve ambiguity.
    The LLM must NEVER fabricate exact quantities or nutrition values.
    """
    food_name: str = Field(..., description="Recognized name of the food item")
    quantity: Optional[Decimal] = Field(
        default=None,
        description="Numeric quantity if explicitly mentioned, or None if ambiguous/unspecified"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measure (e.g., piece, cup, bowl, gram) if mentioned, or None"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Preparation or modifier notes (e.g., 'with butter', 'steamed', 'spicy') if any"
    )

    model_config = ConfigDict(extra="ignore")


class MealExtraction(BaseModel):
    """
    Structured extraction of a meal from natural language input.
    """
    meal_type: Optional[MealType] = Field(
        default=None,
        description="Identified meal type (BREAKFAST, LUNCH, DINNER, SNACK, OTHER) or None"
    )
    items: List[ExtractedMealItem] = Field(
        default_factory=list,
        description="List of extracted food items"
    )

    model_config = ConfigDict(extra="ignore")


class MealExtractionRequest(BaseModel):
    """
    Request schema for the meal extraction endpoint.
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language description of food or meal consumed"
    )


class MealExtractionResponse(BaseModel):
    """
    Response schema for the meal extraction endpoint.
    """
    success: bool = True
    extraction: MealExtraction
    model: str = Field(..., description="Exact LLM model identifier used for extraction")
