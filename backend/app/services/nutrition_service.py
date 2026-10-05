"""
Nutrition service handling daily nutritional aggregation, active goal comparison, and historical analysis.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.meal_service import meal_service
from app.services.goal_service import goal_service
from app.schemas.meal import NutritionTotals
from app.schemas.nutrition import (
    MacroTargets,
    DailyNutritionResponse,
    NutritionHistoryResponse,
)
from app.exceptions.base import ValidationException


class NutritionService:
    @classmethod
    def get_daily_nutrition(
        cls,
        db: Session,
        user_id: int,
        target_date: date,
    ) -> DailyNutritionResponse:
        """
        Aggregate total calories and macronutrients consumed on a calendar date.
        Compares intake with user's active goal to compute remaining targets: max(target - consumed, 0).
        Returns zero values if no meals are logged.
        """
        meals = meal_service.get_meals_for_date(db, user_id=user_id, target_date=target_date)

        total_cal = Decimal("0.00")
        total_pro = Decimal("0.00")
        total_carb = Decimal("0.00")
        total_fat = Decimal("0.00")
        total_fib = Decimal("0.00")

        for meal in meals:
            for item in meal.items:
                total_cal += item.calculated_calories
                total_pro += item.calculated_protein
                total_carb += item.calculated_carbohydrates
                total_fat += item.calculated_fat
                total_fib += item.calculated_fiber

        consumed_totals = NutritionTotals(
            calories=total_cal,
            protein=total_pro,
            carbohydrates=total_carb,
            fat=total_fat,
            fiber=total_fib,
        )

        # Retrieve active goal targets
        goal = goal_service.get_by_user_id(db, user_id)
        target_macros: Optional[MacroTargets] = None
        remaining_macros: Optional[MacroTargets] = None

        if goal and goal.is_active:
            target_cal = Decimal(str(goal.target_calories)) if goal.target_calories is not None else None
            target_pro = Decimal(str(goal.target_protein)) if goal.target_protein is not None else None
            target_carb = Decimal(str(goal.target_carbohydrates)) if goal.target_carbohydrates is not None else None
            target_fat = Decimal(str(goal.target_fat)) if goal.target_fat is not None else None

            target_macros = MacroTargets(
                calories=target_cal,
                protein=target_pro,
                carbohydrates=target_carb,
                fat=target_fat,
            )

            # Compute remaining intake bounded at zero: max(target - consumed, 0)
            def _calc_remaining(target_val: Optional[Decimal], consumed_val: Decimal) -> Optional[Decimal]:
                if target_val is None:
                    return None
                rem = target_val - consumed_val
                return max(Decimal("0.00"), rem)

            remaining_macros = MacroTargets(
                calories=_calc_remaining(target_cal, total_cal),
                protein=_calc_remaining(target_pro, total_pro),
                carbohydrates=_calc_remaining(target_carb, total_carb),
                fat=_calc_remaining(target_fat, total_fat),
            )

        return DailyNutritionResponse(
            date=target_date,
            meals_count=len(meals),
            consumed=consumed_totals,
            target=target_macros,
            remaining=remaining_macros,
        )

    @classmethod
    def get_history(
        cls,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> NutritionHistoryResponse:
        """
        Fetch aggregated daily nutrition for each calendar day across a specified date range.
        Limits query span to a maximum of 31 days to maintain bounded performance.
        """
        if end_date < start_date:
            raise ValidationException("end_date must be on or after start_date.")

        delta_days = (end_date - start_date).days
        if delta_days > 31:
            raise ValidationException("Date range cannot exceed 31 days.")

        daily_records: List[DailyNutritionResponse] = []
        current = start_date
        while current <= end_date:
            daily_records.append(cls.get_daily_nutrition(db, user_id=user_id, target_date=current))
            current += timedelta(days=1)

        return NutritionHistoryResponse(
            start_date=start_date,
            end_date=end_date,
            days=daily_records,
        )


nutrition_service = NutritionService()
