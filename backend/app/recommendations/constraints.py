"""
Deterministic constraint evaluation and candidate scoring for nutrition recommendations.
Enforces strict dietary preferences, allergy exclusions, disliked foods filtering,
ingredient matching, and nutritional target alignment.
"""

from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional, Set
from app.models.food import FoodItem
from app.recommendations.schemas import FoodCandidate, RecommendationRequest

logger = logging.getLogger(__name__)

# Category definitions
MEAT_CATEGORY = "MEAT"
DAIRY_CATEGORY = "DAIRY"
VEGETABLE_CATEGORY = "VEGETABLE"
FRUIT_CATEGORY = "FRUIT"
GRAIN_CATEGORY = "GRAIN"
LEGUME_CATEGORY = "LEGUME"
SNACK_CATEGORY = "SNACK"

# Semantic keywords
NON_VEG_KEYWORDS = {"chicken", "meat", "fish", "mutton", "beef", "pork", "seafood", "prawn", "egg", "lamb"}
DAIRY_KEYWORDS = {"milk", "curd", "paneer", "dahi", "cheese", "yogurt", "ghee", "butter"}


def _text_contains_any(text: str, keywords: Set[str]) -> bool:
    """Check if any keyword appears as a standalone word or token in text."""
    lower_text = text.lower()
    for kw in keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, lower_text):
            return True
    return False


def filter_by_dietary_preference(
    foods: List[FoodItem],
    dietary_preference: Optional[str],
) -> List[FoodItem]:
    """
    Deterministically filters out foods that violate the user's dietary preference.
    - VEGETARIAN / VEG: Excludes MEAT category and foods with meat/egg keywords.
    - VEGAN: Excludes MEAT and DAIRY categories, and foods with animal product keywords.
    - EGGETARIAN: Excludes MEAT category except eggs.
    - NON_VEGETARIAN / None: Retains all food items.
    """
    if not dietary_preference:
        return foods

    pref_clean = dietary_preference.strip().upper().replace("-", "_").replace(" ", "_")
    filtered: List[FoodItem] = []

    for food in foods:
        cat = food.category.upper()
        food_name = food.name.lower()
        desc = (food.description or "").lower()
        full_text = f"{food_name} {desc}"

        if pref_clean in ("VEGETARIAN", "VEG"):
            # Exclude meat category and animal keywords
            if cat == MEAT_CATEGORY or _text_contains_any(full_text, NON_VEG_KEYWORDS):
                continue
            filtered.append(food)

        elif pref_clean == "VEGAN":
            # Exclude meat, dairy, and animal keywords
            if (
                cat in (MEAT_CATEGORY, DAIRY_CATEGORY)
                or _text_contains_any(full_text, NON_VEG_KEYWORDS)
                or _text_contains_any(full_text, DAIRY_KEYWORDS)
            ):
                continue
            filtered.append(food)

        elif pref_clean == "EGGETARIAN":
            # Exclude meat except egg
            if cat == MEAT_CATEGORY and "egg" not in food_name:
                continue
            filtered.append(food)

        else:
            # NON_VEGETARIAN, OTHER, or unconstrained
            filtered.append(food)

    return filtered


def filter_by_allergies(
    foods: List[FoodItem],
    allergies: Optional[List[str]],
) -> List[FoodItem]:
    """
    Excludes any food that contains or matches an allergen in the user's allergy list.
    Conservative: if allergen keyword is present in name, description, or mapped category,
    the food is excluded.
    """
    if not allergies:
        return foods

    clean_allergens = [a.strip().lower() for a in allergies if a and a.strip()]
    if not clean_allergens:
        return foods

    filtered: List[FoodItem] = []

    for food in foods:
        food_name = food.name.lower()
        desc = (food.description or "").lower()
        cat = food.category.upper()
        has_allergen = False

        for allergen in clean_allergens:
            # Category-based mappings
            if allergen in ("dairy", "milk", "lactose") and (cat == DAIRY_CATEGORY or _text_contains_any(f"{food_name} {desc}", DAIRY_KEYWORDS)):
                has_allergen = True
                break
            if allergen in ("nuts", "peanut", "peanuts", "almond", "almonds") and _text_contains_any(f"{food_name} {desc}", {"nut", "nuts", "peanut", "peanuts", "almond", "almonds"}):
                has_allergen = True
                break
            if allergen in ("egg", "eggs") and "egg" in food_name:
                has_allergen = True
                break
            if allergen in ("gluten", "wheat") and ("chapati" in food_name or "bread" in food_name or "wheat" in desc):
                has_allergen = True
                break

            # Direct word match against food name or description
            pattern = rf"\b{re.escape(allergen)}\b"
            if re.search(pattern, food_name) or re.search(pattern, desc):
                has_allergen = True
                break

        if not has_allergen:
            filtered.append(food)

    return filtered


def filter_by_disliked_foods(
    foods: List[FoodItem],
    disliked_foods: Optional[List[str]],
) -> List[FoodItem]:
    """
    Filters out foods explicitly listed in the user's disliked foods list.
    """
    if not disliked_foods:
        return foods

    clean_disliked = [d.strip().lower() for d in disliked_foods if d and d.strip()]
    if not clean_disliked:
        return foods

    filtered: List[FoodItem] = []

    for food in foods:
        food_name = food.name.lower()
        desc = (food.description or "").lower()
        is_disliked = False

        for disliked in clean_disliked:
            pattern = rf"\b{re.escape(disliked)}\b"
            if re.search(pattern, food_name) or re.search(pattern, desc):
                is_disliked = True
                break

        if not is_disliked:
            filtered.append(food)

    # If filtering disliked foods would leave too few items (less than 2), fall back to original
    if len(filtered) < 2 and len(foods) >= 2:
        logger.info("Disliked foods filter would leave too few candidates (%d); keeping non-disliked prioritized", len(filtered))
        return foods

    return filtered


def _matches_any_ingredient(food: FoodItem, ingredients: List[str]) -> bool:
    """Check if food name or description matches any requested ingredient."""
    food_name = food.name.lower()
    desc = (food.description or "").lower()
    full_text = f"{food_name} {desc}"

    for ing in ingredients:
        clean_ing = ing.strip().lower()
        if not clean_ing:
            continue
        pattern = rf"\b{re.escape(clean_ing)}\b"
        if re.search(pattern, full_text):
            return True
    return False


def score_and_rank_candidates(
    foods: List[FoodItem],
    request: RecommendationRequest,
    context_data: Dict[str, Any],
    max_candidates: int = 8,
) -> List[FoodCandidate]:
    """
    Scores and ranks candidate foods deterministically based on:
    - Available ingredients matching
    - Meal type suitability
    - Nutritional focus (high_protein, low_calorie, balanced, light)
    - Remaining calorie fit
    """
    available_ingredients: List[str] = context_data.get("available_ingredients", [])
    remaining_calories: Optional[Decimal] = context_data.get("remaining_calories")
    goal_type: Optional[str] = context_data.get("goal_type")
    focus: Optional[str] = (request.focus or "").lower()
    meal_type: Optional[str] = (request.meal_type or "").upper()

    scored_items: List[tuple[Decimal, FoodItem, List[str]]] = []

    for food in foods:
        score = Decimal("10.00")
        reasons: List[str] = []

        # 1. Available Ingredients Match
        if available_ingredients and _matches_any_ingredient(food, available_ingredients):
            score += Decimal("60.00")
            reasons.append("Matches your available ingredients")

        # 2. Meal Type Suitability
        food_name = food.name.lower()
        cat = food.category.upper()

        if meal_type == "BREAKFAST":
            if any(k in food_name for k in ("idli", "dosa", "oats", "banana", "egg", "milk")):
                score += Decimal("25.00")
                reasons.append("Great breakfast option")
        elif meal_type in ("LUNCH", "DINNER"):
            if any(k in food_name for k in ("rice", "chapati", "dal", "paneer", "chicken", "vegetables", "sambar")):
                score += Decimal("25.00")
                reasons.append(f"Classic {meal_type.lower()} staple")
        elif meal_type == "SNACK":
            if any(k in food_name for k in ("almonds", "peanuts", "apple", "banana", "curd")):
                score += Decimal("30.00")
                reasons.append("Convenient nutritious snack")

        # 3. Nutritional Focus Alignment
        is_high_protein = (
            focus == "high_protein"
            or goal_type == "MUSCLE_GAIN"
            or "protein" in (request.notes or "").lower()
        )
        is_low_calorie = (
            focus in ("low_calorie", "light")
            or goal_type == "WEIGHT_LOSS"
        )

        if is_high_protein:
            # Score heavily by protein content and protein density
            if food.protein >= Decimal("15.00"):
                score += Decimal("40.00")
                reasons.append(f"High protein: {food.protein}g protein per serving")
            elif food.protein >= Decimal("6.00"):
                score += Decimal("20.00")
                reasons.append(f"Good protein source: {food.protein}g protein")
            # Protein-to-calorie ratio bonus
            if food.calories > Decimal("0.00"):
                density = (food.protein / food.calories) * Decimal("100.00")
                score += min(density, Decimal("30.00"))

        elif is_low_calorie:
            if food.calories <= Decimal("100.00"):
                score += Decimal("35.00")
                reasons.append(f"Low calorie: {food.calories} kcal per serving")
            elif food.calories <= Decimal("150.00"):
                score += Decimal("15.00")
                reasons.append(f"Moderate calorie: {food.calories} kcal per serving")
            if food.fiber >= Decimal("2.00"):
                score += Decimal("10.00")
                reasons.append(f"High fiber ({food.fiber}g) for satiety")

        else:
            # Balanced focus
            if food.fiber >= Decimal("2.00"):
                score += Decimal("10.00")
            if food.protein >= Decimal("5.00"):
                score += Decimal("10.00")

        # 4. Remaining Calorie Fit
        if remaining_calories is not None:
            if remaining_calories > Decimal("0.00"):
                if food.calories <= remaining_calories:
                    score += Decimal("15.00")
                    reasons.append(f"Fits within your remaining {remaining_calories} kcal budget")
                else:
                    score -= Decimal("15.00")
            else:
                # Target already reached or exceeded
                if food.calories <= Decimal("80.00"):
                    score += Decimal("25.00")
                    reasons.append("Very light option fitting exceeded calorie target")
                else:
                    score -= Decimal("20.00")

        if not reasons:
            reasons.append(f"Balanced {cat.lower()} option with {food.calories} kcal and {food.protein}g protein")

        scored_items.append((score, food, reasons))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    # Pick top candidates with category diversity
    selected_candidates: List[FoodCandidate] = []
    category_counts: Dict[str, int] = {}

    for _, food, reasons in scored_items:
        cat = food.category.upper()
        current_cat_count = category_counts.get(cat, 0)

        # Allow at most 2 items per category unless we have too few candidates
        if current_cat_count >= 2 and len(selected_candidates) < (max_candidates - 2):
            continue

        category_counts[cat] = current_cat_count + 1
        selected_candidates.append(
            FoodCandidate(
                id=food.id,
                name=food.name,
                category=food.category,
                serving_size=food.serving_size,
                serving_unit=food.serving_unit,
                calories=food.calories,
                protein=food.protein,
                carbohydrates=food.carbohydrates,
                fat=food.fat,
                fiber=food.fiber,
                suggested_quantity=Decimal("1.00"),
                suggested_unit=food.serving_unit,
                reasons=reasons,
            )
        )

        if len(selected_candidates) >= max_candidates:
            break

    # If category constraint was too strict, backfill
    if len(selected_candidates) < min(max_candidates, len(foods)):
        seen_ids = {c.id for c in selected_candidates}
        for _, food, reasons in scored_items:
            if food.id not in seen_ids:
                selected_candidates.append(
                    FoodCandidate(
                        id=food.id,
                        name=food.name,
                        category=food.category,
                        serving_size=food.serving_size,
                        serving_unit=food.serving_unit,
                        calories=food.calories,
                        protein=food.protein,
                        carbohydrates=food.carbohydrates,
                        fat=food.fat,
                        fiber=food.fiber,
                        suggested_quantity=Decimal("1.00"),
                        suggested_unit=food.serving_unit,
                        reasons=reasons,
                    )
                )
                if len(selected_candidates) >= max_candidates:
                    break

    return selected_candidates
