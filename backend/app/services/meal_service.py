"""
Meal service handling meal creation, transaction management, nutrition snapshots, and queries.
"""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.food import FoodItem
from app.models.meal import Meal, MealItem
from app.schemas.meal import (
    MealCreate,
    MealResponse,
    MealItemResponse,
    NutritionTotals,
)
from app.nutrition.calculator import nutrition_calculator
from app.exceptions.base import ResourceNotFoundException


class MealService:
    @staticmethod
    def format_meal_response(meal: Meal) -> MealResponse:
        """Helper to format a Meal entity into a MealResponse with computed totals."""
        total_cal = Decimal("0.00")
        total_pro = Decimal("0.00")
        total_carb = Decimal("0.00")
        total_fat = Decimal("0.00")
        total_fib = Decimal("0.00")

        item_responses: List[MealItemResponse] = []
        for item in meal.items:
            total_cal += item.calculated_calories
            total_pro += item.calculated_protein
            total_carb += item.calculated_carbohydrates
            total_fat += item.calculated_fat
            total_fib += item.calculated_fiber

            item_responses.append(
                MealItemResponse(
                    id=item.id,
                    food_item_id=item.food_item_id,
                    food_name=item.food_item.name if item.food_item else "Unknown Food",
                    quantity=item.quantity,
                    unit=item.unit,
                    calculated_calories=item.calculated_calories,
                    calculated_protein=item.calculated_protein,
                    calculated_carbohydrates=item.calculated_carbohydrates,
                    calculated_fat=item.calculated_fat,
                    calculated_fiber=item.calculated_fiber,
                    created_at=item.created_at,
                )
            )

        return MealResponse(
            id=meal.id,
            user_id=meal.user_id,
            meal_type=meal.meal_type,
            consumed_at=meal.consumed_at,
            items=item_responses,
            totals=NutritionTotals(
                calories=total_cal,
                protein=total_pro,
                carbohydrates=total_carb,
                fat=total_fat,
                fiber=total_fib,
            ),
            created_at=meal.created_at,
            updated_at=meal.updated_at,
        )

    @classmethod
    def create_meal(cls, db: Session, user_id: int, meal_in: MealCreate) -> MealResponse:
        """
        Atomically create a meal and all constituent meal items.
        Calculates and stores an immutable nutrition snapshot for each item at logging time.
        If any item validation fails (e.g. food not found or unit mismatch), the entire transaction rolls back.
        """
        # Step 1: Pre-validate all items and calculate nutrition snapshots in memory
        prepared_items = []
        for item_in in meal_in.items:
            food = db.get(FoodItem, item_in.food_id)
            if not food:
                raise ResourceNotFoundException("FoodItem", item_in.food_id)

            calc_result = nutrition_calculator.calculate(
                food=food,
                quantity=item_in.quantity,
                unit=item_in.unit,
            )
            prepared_items.append((item_in, calc_result))

        # Step 2: Atomic database persistence
        try:
            meal = Meal(
                user_id=user_id,
                meal_type=meal_in.meal_type,
                consumed_at=meal_in.consumed_at or datetime.now(timezone.utc),
            )
            db.add(meal)
            db.flush()  # Generates meal.id

            for item_in, calc in prepared_items:
                meal_item = MealItem(
                    meal_id=meal.id,
                    food_item_id=calc.food_id,
                    quantity=calc.quantity,
                    unit=calc.unit,
                    calculated_calories=calc.calories,
                    calculated_protein=calc.protein,
                    calculated_carbohydrates=calc.carbohydrates,
                    calculated_fat=calc.fat,
                    calculated_fiber=calc.fiber,
                )
                db.add(meal_item)

            db.commit()
            db.refresh(meal)
            return cls.format_meal_response(meal)
        except Exception:
            db.rollback()
            raise

    @classmethod
    def get_by_id(cls, db: Session, user_id: int, meal_id: int) -> Optional[Meal]:
        """Fetch a specific meal scoped strictly to the authenticated user."""
        stmt = (
            select(Meal)
            .where(Meal.id == meal_id, Meal.user_id == user_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def get_user_meals(
        cls,
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Meal]:
        """Fetch paginated meal history for the authenticated user."""
        safe_limit = max(1, min(limit, 100))
        stmt = (
            select(Meal)
            .where(Meal.user_id == user_id)
            .order_by(Meal.consumed_at.desc())
            .limit(safe_limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars().all())

    @classmethod
    def get_meals_for_date(
        cls,
        db: Session,
        user_id: int,
        target_date: date,
    ) -> List[Meal]:
        """
        Fetch all meals consumed by the user within a 24-hour UTC calendar date boundary.
        """
        start_utc = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
        end_utc = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)

        stmt = (
            select(Meal)
            .where(
                Meal.user_id == user_id,
                Meal.consumed_at >= start_utc,
                Meal.consumed_at <= end_utc,
            )
            .order_by(Meal.consumed_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @classmethod
    def delete_meal(cls, db: Session, user_id: int, meal_id: int) -> bool:
        """Delete a meal owned by the user. Returns False if meal does not exist."""
        meal = cls.get_by_id(db, user_id=user_id, meal_id=meal_id)
        if meal is None:
            return False
        db.delete(meal)
        db.commit()
        return True


meal_service = MealService()
