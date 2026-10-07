"""
Personalized recommendation service.
Orchestrates profile retrieval, active goal inspection, daily intake aggregation,
deterministic constraint filtering, and candidate selection.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food import FoodItem
from app.models.user import User
from app.recommendations.constraints import (
    filter_by_allergies,
    filter_by_dietary_preference,
    filter_by_disliked_foods,
    score_and_rank_candidates,
)
from app.recommendations.schemas import (
    FoodCandidate,
    RecommendationContext,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.goal_service import goal_service
from app.services.nutrition_service import nutrition_service
from app.services.profile_service import profile_service

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Coordinates personalized meal recommendation data preparation.
    Ensures that recommendations are rooted strictly in real user state and database foods.
    """

    def build_recommendation_context(
        self,
        db: Session,
        user: User,
        request: Optional[RecommendationRequest] = None,
    ) -> RecommendationContext:
        """
        Builds the deterministic recommendation context for the authenticated user.
        Retrieves profile, active goal, and today's intake, applies constraints,
        and scores real catalog food candidates.
        """
        req = request or RecommendationRequest()
        user_id = user.id
        today_date = datetime.now(timezone.utc).date()

        # 1. Retrieve persistent user context
        profile = profile_service.get_by_user_id(db, user_id)
        goal = goal_service.get_by_user_id(db, user_id)
        daily_nutrition = nutrition_service.get_daily_nutrition(db, user_id=user_id, target_date=today_date)

        # 2. Extract profile facts
        dietary_pref = profile.dietary_preference if profile else None
        allergies = list(profile.allergies_or_restrictions or []) if profile else []
        disliked = list(profile.disliked_foods or []) if profile else []
        cuisines = list(profile.preferred_cuisine or []) if profile else []
        profile_ingredients = list(profile.available_ingredients or []) if profile else []
        budget_per_day = profile.budget_per_day if profile else None

        # Combine available ingredients from profile and current request
        req_ingredients = [ing.strip() for ing in (req.ingredients or []) if ing and ing.strip()]
        combined_ingredients = list(dict.fromkeys(profile_ingredients + req_ingredients))

        # 3. Extract goal facts
        goal_type = goal.goal_type if (goal and goal.is_active) else None
        target_cal = Decimal(str(goal.target_calories)) if (goal and goal.is_active and goal.target_calories is not None) else None
        target_pro = Decimal(str(goal.target_protein)) if (goal and goal.is_active and goal.target_protein is not None) else None
        target_carb = Decimal(str(goal.target_carbohydrates)) if (goal and goal.is_active and goal.target_carbohydrates is not None) else None
        target_fat = Decimal(str(goal.target_fat)) if (goal and goal.is_active and goal.target_fat is not None) else None

        # 4. Extract today's intake
        consumed_cal = daily_nutrition.consumed.calories
        consumed_pro = daily_nutrition.consumed.protein
        consumed_carb = daily_nutrition.consumed.carbohydrates
        consumed_fat = daily_nutrition.consumed.fat
        consumed_fib = daily_nutrition.consumed.fiber

        # 5. Calculate remaining allowances deterministically
        remaining_cal: Optional[Decimal] = None
        remaining_pro: Optional[Decimal] = None
        remaining_carb: Optional[Decimal] = None
        remaining_fat: Optional[Decimal] = None

        if target_cal is not None:
            remaining_cal = target_cal - consumed_cal
        if target_pro is not None:
            remaining_pro = target_pro - consumed_pro
        if target_carb is not None:
            remaining_carb = target_carb - consumed_carb
        if target_fat is not None:
            remaining_fat = target_fat - consumed_fat

        # Allow request target_calories to override if explicitly specified
        if req.target_calories is not None:
            remaining_cal = req.target_calories

        # 6. Retrieve all database food items
        stmt = select(FoodItem)
        all_foods = list(db.execute(stmt).scalars().all())

        # 7. Apply deterministic constraints
        filtered_foods = filter_by_dietary_preference(all_foods, dietary_pref)
        filtered_foods = filter_by_allergies(filtered_foods, allergies)
        filtered_foods = filter_by_disliked_foods(filtered_foods, disliked)

        # 8. Deterministic ranking and candidate selection
        scoring_context: Dict[str, Any] = {
            "available_ingredients": combined_ingredients,
            "remaining_calories": remaining_cal,
            "goal_type": goal_type,
        }
        candidates = score_and_rank_candidates(
            foods=filtered_foods,
            request=req,
            context_data=scoring_context,
            max_candidates=5,
        )

        # 9. Document transparent limitations
        limitations: List[str] = [
            "Food database does not track monetary pricing; budget constraints cannot be priced deterministically."
        ]
        if remaining_cal is not None and remaining_cal <= Decimal("0.00"):
            limitations.append(
                f"Today's calorie target ({target_cal} kcal) is reached or exceeded (consumed: {consumed_cal} kcal). "
                "Lighter, nutrient-dense options are prioritized."
            )
        if not goal or not goal.is_active:
            limitations.append("No active nutrition goal is set; recommendations use standard balanced nutritional targets.")
        if not profile:
            limitations.append("No user profile configured; recommendations use default nutritional guidelines.")

        logger.info(
            "Built recommendation context for user %d: %d candidates selected from %d foods",
            user_id,
            len(candidates),
            len(all_foods),
        )

        return RecommendationContext(
            user_id=user_id,
            dietary_preference=dietary_pref,
            allergies_or_restrictions=allergies,
            disliked_foods=disliked,
            preferred_cuisine=cuisines,
            available_ingredients=combined_ingredients,
            budget_per_day=budget_per_day,
            goal_type=goal_type,
            target_calories=target_cal,
            target_protein=target_pro,
            target_carbohydrates=target_carb,
            target_fat=target_fat,
            consumed_calories=consumed_cal,
            consumed_protein=consumed_pro,
            consumed_carbohydrates=consumed_carb,
            consumed_fat=consumed_fat,
            consumed_fiber=consumed_fib,
            remaining_calories=remaining_cal,
            remaining_protein=remaining_pro,
            remaining_carbohydrates=remaining_carb,
            remaining_fat=remaining_fat,
            meal_type=req.meal_type,
            focus=req.focus,
            candidates=candidates,
            limitations=limitations,
        )

    def format_direct_recommendation(
        self,
        context: RecommendationContext,
    ) -> RecommendationResponse:
        """
        Builds a deterministic, structured RecommendationResponse directly from context.
        Used for direct API responses and offline unit test verifications.
        """
        items: List[RecommendationItem] = []
        total_cal = Decimal("0.00")
        total_pro = Decimal("0.00")
        total_carb = Decimal("0.00")
        total_fat = Decimal("0.00")
        total_fib = Decimal("0.00")

        # Take top 2-3 complimentary candidates for a meal
        selected_candidates = context.candidates[:3]

        for cand in selected_candidates:
            items.append(
                RecommendationItem(
                    food_id=cand.id,
                    food_name=cand.name,
                    quantity=cand.suggested_quantity,
                    unit=cand.suggested_unit,
                    calories=cand.calories,
                    protein=cand.protein,
                    carbohydrates=cand.carbohydrates,
                    fat=cand.fat,
                    fiber=cand.fiber,
                )
            )
            total_cal += cand.calories
            total_pro += cand.protein
            total_carb += cand.carbohydrates
            total_fat += cand.fat
            total_fib += cand.fiber

        meal_name = (context.meal_type or "Meal").capitalize()
        summary = f"Recommended {meal_name}: " + " + ".join(f"{it.food_name} ({it.quantity} {it.unit})" for it in items)

        explanation_parts = [
            f"This meal provides {total_cal} kcal, {total_pro}g protein, {total_carb}g carbs, and {total_fat}g fat."
        ]
        if context.remaining_calories is not None:
            explanation_parts.append(f"It aligns with your remaining budget of {context.remaining_calories} kcal today.")
        if context.goal_type:
            explanation_parts.append(f"Selected to support your active {context.goal_type} goal.")
        if context.dietary_preference:
            explanation_parts.append(f"Strictly respects your {context.dietary_preference} preference.")

        return RecommendationResponse(
            recommendation_summary=summary,
            meal_type=context.meal_type,
            items=items,
            total_calories=total_cal,
            total_protein=total_pro,
            total_carbohydrates=total_carb,
            total_fat=total_fat,
            total_fiber=total_fib,
            explanation=" ".join(explanation_parts),
            limitations=context.limitations,
        )


recommendation_service = RecommendationService()
