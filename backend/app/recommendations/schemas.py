"""
Pydantic schemas for personalized nutrition recommendations.
Defines structured input requests, food candidate representations,
and complete serializable recommendation context.
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """Input parameters for a meal recommendation request."""
    meal_type: Optional[str] = Field(None, description="Target meal type: BREAKFAST, LUNCH, DINNER, SNACK, or OTHER")
    focus: Optional[str] = Field(None, description="Nutritional focus, e.g. high_protein, low_calorie, balanced, light")
    target_calories: Optional[Decimal] = Field(None, ge=0, description="Specific target calories for this meal / remaining")
    ingredients: Optional[List[str]] = Field(default_factory=list, description="Specific ingredients user has or wants to use")
    notes: Optional[str] = Field(None, description="Optional conversational request notes")


class FoodCandidate(BaseModel):
    """Authoritative candidate food item derived from the database catalog."""
    id: int = Field(..., description="FoodItem database ID")
    name: str = Field(..., description="Food name")
    category: str = Field(..., description="Food category (e.g. GRAIN, LEGUME, DAIRY, MEAT, VEGETABLE, FRUIT)")
    serving_size: Decimal = Field(..., description="Base serving quantity")
    serving_unit: str = Field(..., description="Base serving unit (e.g. gram, piece, ml, cup)")
    calories: Decimal = Field(..., description="Calories per serving in kcal")
    protein: Decimal = Field(..., description="Protein per serving in grams")
    carbohydrates: Decimal = Field(..., description="Carbohydrates per serving in grams")
    fat: Decimal = Field(..., description="Fat per serving in grams")
    fiber: Decimal = Field(default=Decimal("0.00"), description="Dietary fiber per serving in grams")
    suggested_quantity: Decimal = Field(default=Decimal("1.00"), description="Suggested portion quantity")
    suggested_unit: str = Field(..., description="Suggested serving unit")
    reasons: List[str] = Field(default_factory=list, description="Deterministic reasons why this food was selected")


class RecommendationContext(BaseModel):
    """
    Complete serializable recommendation context provided to the LLM.
    Contains real user facts, active goals, consumed/remaining nutrition,
    deterministic constraints applied, and candidate food items.
    """
    user_id: int
    dietary_preference: Optional[str] = None
    allergies_or_restrictions: List[str] = Field(default_factory=list)
    disliked_foods: List[str] = Field(default_factory=list)
    preferred_cuisine: List[str] = Field(default_factory=list)
    available_ingredients: List[str] = Field(default_factory=list)
    budget_per_day: Optional[float] = None

    # Goal facts
    goal_type: Optional[str] = None
    target_calories: Optional[Decimal] = None
    target_protein: Optional[Decimal] = None
    target_carbohydrates: Optional[Decimal] = None
    target_fat: Optional[Decimal] = None

    # Today's consumed intake
    consumed_calories: Decimal = Decimal("0.00")
    consumed_protein: Decimal = Decimal("0.00")
    consumed_carbohydrates: Decimal = Decimal("0.00")
    consumed_fat: Decimal = Decimal("0.00")
    consumed_fiber: Decimal = Decimal("0.00")

    # Deterministic remaining allowance
    remaining_calories: Optional[Decimal] = None
    remaining_protein: Optional[Decimal] = None
    remaining_carbohydrates: Optional[Decimal] = None
    remaining_fat: Optional[Decimal] = None

    # Request parameters
    meal_type: Optional[str] = None
    focus: Optional[str] = None

    # Filtered and ranked food candidates
    candidates: List[FoodCandidate] = Field(default_factory=list)

    # Transparent operational notes & limitations
    limitations: List[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    """Structured item in a finalized meal recommendation."""
    food_id: int
    food_name: str
    quantity: Decimal
    unit: str
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal


class RecommendationResponse(BaseModel):
    """Complete recommendation response with itemized meal and nutritional totals."""
    recommendation_summary: str
    meal_type: Optional[str] = None
    items: List[RecommendationItem] = Field(default_factory=list)
    total_calories: Decimal = Decimal("0.00")
    total_protein: Decimal = Decimal("0.00")
    total_carbohydrates: Decimal = Decimal("0.00")
    total_fat: Decimal = Decimal("0.00")
    total_fiber: Decimal = Decimal("0.00")
    explanation: str
    limitations: List[str] = Field(default_factory=list)
