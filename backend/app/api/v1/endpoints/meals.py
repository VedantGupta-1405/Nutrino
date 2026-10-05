"""
Meal logging, retrieval, and deletion endpoints.
All operations are scoped to the authenticated user.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.meal import MealCreate, MealResponse
from app.services.meal_service import meal_service
from app.exceptions.base import ResourceNotFoundException

router = APIRouter()


@router.post(
    "",
    response_model=MealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a meal",
    description="Atomically creates a meal with multiple food items. Computes immutable nutrition snapshot at logging time.",
)
def create_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealResponse:
    return meal_service.create_meal(
        db=db,
        user_id=current_user.id,
        meal_in=meal_in,
    )


@router.get(
    "",
    response_model=List[MealResponse],
    summary="List logged meals",
    description="Returns paginated meal records for the authenticated user, ordered newest first.",
)
def list_meals(
    limit: int = Query(50, ge=1, le=100, description="Max meals to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MealResponse]:
    meals = meal_service.get_user_meals(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return [meal_service.format_meal_response(m) for m in meals]


@router.get(
    "/today",
    response_model=List[MealResponse],
    summary="Get today's meals",
    description="Retrieves all meals consumed by the authenticated user on the current UTC calendar date.",
)
def get_todays_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MealResponse]:
    today_utc = datetime.now(timezone.utc).date()
    meals = meal_service.get_meals_for_date(
        db=db,
        user_id=current_user.id,
        target_date=today_utc,
    )
    return [meal_service.format_meal_response(m) for m in meals]


@router.get(
    "/{meal_id}",
    response_model=MealResponse,
    summary="Get meal by ID",
    description="Retrieve a specific meal record with full nutritional breakdown. Scoped to the authenticated user.",
)
def get_meal_by_id(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealResponse:
    meal = meal_service.get_by_id(db, user_id=current_user.id, meal_id=meal_id)
    if meal is None:
        raise ResourceNotFoundException("Meal", meal_id)
    return meal_service.format_meal_response(meal)


@router.delete(
    "/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a meal",
    description="Permanently deletes a logged meal and its associated meal items. Only the meal owner can delete.",
)
def delete_meal(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = meal_service.delete_meal(db, user_id=current_user.id, meal_id=meal_id)
    if not deleted:
        raise ResourceNotFoundException("Meal", meal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
