"""
Food lookup and search endpoints.
Publicly accessible read-only food catalog.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.food import FoodItemResponse
from app.services.food_service import food_service
from app.exceptions.base import ResourceNotFoundException

router = APIRouter()


@router.get(
    "/search",
    response_model=List[FoodItemResponse],
    summary="Search food catalog",
    description="Case-insensitive search over food names and descriptions with relevance ranking and category filtering.",
)
def search_foods(
    q: str = Query(..., min_length=1, max_length=100, description="Food name search query"),
    category: Optional[str] = Query(None, description="Optional category filter (e.g. GRAIN, DAIRY)"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> List[FoodItemResponse]:
    foods = food_service.search(
        db=db,
        query=q,
        category=category,
        limit=limit,
        offset=offset,
    )
    return [FoodItemResponse.model_validate(f) for f in foods]


@router.get(
    "/{food_id}",
    response_model=FoodItemResponse,
    summary="Get food item by ID",
    description="Retrieve full nutritional breakdown and serving basis for a specific food item.",
)
def get_food_by_id(
    food_id: int,
    db: Session = Depends(get_db),
) -> FoodItemResponse:
    food = food_service.get_by_id(db, food_id=food_id)
    if food is None:
        raise ResourceNotFoundException("FoodItem", food_id)
    return FoodItemResponse.model_validate(food)
