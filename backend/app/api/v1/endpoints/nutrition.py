"""
Nutrition aggregation endpoints for daily intake, active target comparison, and history.
"""

from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.nutrition import (
    DailyNutritionResponse,
    NutritionHistoryResponse,
)
from app.services.nutrition_service import nutrition_service

router = APIRouter()


@router.get(
    "/today",
    response_model=DailyNutritionResponse,
    summary="Get today's aggregated nutrition",
    description="Aggregates consumed calories and macronutrients for today (UTC), comparing with active goal targets.",
)
def get_today_nutrition(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyNutritionResponse:
    today_utc = datetime.now(timezone.utc).date()
    return nutrition_service.get_daily_nutrition(
        db=db,
        user_id=current_user.id,
        target_date=today_utc,
    )


@router.get(
    "",
    response_model=DailyNutritionResponse,
    summary="Get aggregated nutrition for a specific date",
    description="Aggregates consumed nutrition and compares against active goal targets for a specified calendar date.",
)
def get_nutrition_by_date(
    date_val: Optional[date] = Query(None, alias="date", description="Target calendar date (defaults to today UTC)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyNutritionResponse:
    target_date = date_val or datetime.now(timezone.utc).date()
    return nutrition_service.get_daily_nutrition(
        db=db,
        user_id=current_user.id,
        target_date=target_date,
    )


@router.get(
    "/history",
    response_model=NutritionHistoryResponse,
    summary="Get historical daily nutrition",
    description="Aggregates daily nutrition over a requested date range (up to 31 days).",
)
def get_nutrition_history(
    start_date: date = Query(..., description="Start of date range (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End of date range (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NutritionHistoryResponse:
    return nutrition_service.get_history(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
