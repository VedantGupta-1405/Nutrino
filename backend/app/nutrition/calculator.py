"""
Deterministic nutrition calculation engine.
Strictly decoupled from FastAPI, LLM prompts, LangGraph, and Ollama.
Performs exact numeric scaling and defensible unit conversions.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Union
from app.models.food import FoodItem
from app.schemas.food import NutritionCalculationResult
from app.exceptions.base import ValidationException

# Unit alias mappings to canonical standard representations
UNIT_ALIASES: Dict[str, str] = {
    # Weight
    "g": "gram",
    "gram": "gram",
    "grams": "gram",
    "gm": "gram",
    "gms": "gram",
    "kg": "kilogram",
    "kilogram": "kilogram",
    "kilograms": "kilogram",
    "mg": "milligram",
    "milligram": "milligram",
    "milligrams": "milligram",
    # Volume
    "ml": "milliliter",
    "milliliter": "milliliter",
    "milliliters": "milliliter",
    "l": "liter",
    "liter": "liter",
    "liters": "liter",
    # Culinary volumetric units
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tablespoon",
    "tablespoon": "tablespoon",
    "tablespoons": "tablespoon",
    "tsp": "teaspoon",
    "teaspoon": "teaspoon",
    "teaspoons": "teaspoon",
    # Portions / count
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "slice": "slice",
    "slices": "slice",
    "serving": "serving",
    "servings": "serving",
    "bowl": "bowl",
    "bowls": "bowl",
    "plate": "plate",
    "plates": "plate",
    "roti": "piece",
    "dosa": "piece",
    "idli": "piece",
    "egg": "piece",
}

# Conversion multipliers to base units within the same dimension
WEIGHT_FACTORS: Dict[str, Decimal] = {
    "gram": Decimal("1.0"),
    "kilogram": Decimal("1000.0"),
    "milligram": Decimal("0.001"),
}

VOLUME_FACTORS: Dict[str, Decimal] = {
    "milliliter": Decimal("1.0"),
    "liter": Decimal("1000.0"),
}

CULINARY_VOLUME_FACTORS: Dict[str, Decimal] = {
    "cup": Decimal("48.0"),          # 1 cup = 48 tsp
    "tablespoon": Decimal("3.0"),     # 1 tbsp = 3 tsp
    "teaspoon": Decimal("1.0"),       # 1 tsp
}


def normalize_unit(unit_str: str) -> str:
    """Normalize input string to canonical unit identifier."""
    cleaned = unit_str.strip().lower()
    return UNIT_ALIASES.get(cleaned, cleaned)


def compute_scaling_factor(
    serving_size: Decimal,
    serving_unit: str,
    requested_quantity: Decimal,
    requested_unit: str,
    food_name: str = "food",
) -> Decimal:
    """
    Deterministically compute the scaling ratio between requested amount and defined serving basis.
    Raises ValidationException if the units belong to incompatible dimensions.
    """
    if requested_quantity <= 0:
        raise ValidationException("Quantity must be greater than zero.")

    if serving_size <= 0:
        raise ValidationException(f"Invalid serving size {serving_size} configured for food item.")

    norm_serving = normalize_unit(serving_unit)
    norm_requested = normalize_unit(requested_unit)

    # 1. Direct match (same unit or canonical alias)
    if norm_serving == norm_requested:
        return requested_quantity / serving_size

    # 2. Weight-to-weight conversion (e.g., kg <-> gram)
    if norm_serving in WEIGHT_FACTORS and norm_requested in WEIGHT_FACTORS:
        base_serving_g = serving_size * WEIGHT_FACTORS[norm_serving]
        base_requested_g = requested_quantity * WEIGHT_FACTORS[norm_requested]
        return base_requested_g / base_serving_g

    # 3. Volume-to-volume conversion (e.g., liter <-> ml)
    if norm_serving in VOLUME_FACTORS and norm_requested in VOLUME_FACTORS:
        base_serving_ml = serving_size * VOLUME_FACTORS[norm_serving]
        base_requested_ml = requested_quantity * VOLUME_FACTORS[norm_requested]
        return base_requested_ml / base_serving_ml

    # 4. Culinary volume conversion (e.g., cup <-> tablespoon <-> teaspoon)
    if norm_serving in CULINARY_VOLUME_FACTORS and norm_requested in CULINARY_VOLUME_FACTORS:
        base_serving_tsp = serving_size * CULINARY_VOLUME_FACTORS[norm_serving]
        base_requested_tsp = requested_quantity * CULINARY_VOLUME_FACTORS[norm_requested]
        return base_requested_tsp / base_serving_tsp

    # Incompatible dimensions (e.g. piece vs gram, or gram vs ml without density)
    raise ValidationException(
        f"Cannot convert requested unit '{requested_unit}' to defined serving unit "
        f"'{serving_unit}' for '{food_name}'. Please use matching units or exact piece/serving counts."
    )


class NutritionCalculator:
    """Deterministic calculator for scaling food item nutritional values."""

    @staticmethod
    def calculate(
        food: FoodItem,
        quantity: Union[Decimal, float, int, str],
        unit: str,
    ) -> NutritionCalculationResult:
        """
        Calculate calories, protein, carbs, fat, and fiber for a given food and portion.
        All calculations preserve decimal precision and round half-up to 2 decimal places.
        """
        dec_qty = Decimal(str(quantity))
        dec_serving_size = Decimal(str(food.serving_size))

        ratio = compute_scaling_factor(
            serving_size=dec_serving_size,
            serving_unit=food.serving_unit,
            requested_quantity=dec_qty,
            requested_unit=unit,
            food_name=food.name,
        )

        def _scale(value: Decimal) -> Decimal:
            scaled = Decimal(str(value)) * ratio
            return scaled.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return NutritionCalculationResult(
            food_id=food.id,
            food_name=food.name,
            quantity=dec_qty,
            unit=unit.strip(),
            serving_basis=f"{food.serving_size} {food.serving_unit}",
            calories=_scale(food.calories),
            protein=_scale(food.protein),
            carbohydrates=_scale(food.carbohydrates),
            fat=_scale(food.fat),
            fiber=_scale(food.fiber),
        )


nutrition_calculator = NutritionCalculator()
