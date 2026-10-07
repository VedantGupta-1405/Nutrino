"""
FastAPI router for direct personalized meal recommendations.
Provides an authenticated endpoint for retrieving deterministic recommendation context and candidate items.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.recommendations.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.recommendations.service import recommendation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized meal recommendation",
    description=(
        "Generates a personalized meal recommendation based on the authenticated user's "
        "dietary preferences, active goal, remaining calories/macros, and available ingredients. "
        "Strictly read-only: does not modify or log meals."
    ),
)
def get_meal_recommendation(
    payload: RecommendationRequest = RecommendationRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """
    Retrieves recommendation context and formats a structured meal recommendation.
    """
    logger.info("Recommendation requested for user %d (meal_type: %s, focus: %s)", current_user.id, payload.meal_type, payload.focus)
    context = recommendation_service.build_recommendation_context(
        db=db,
        user=current_user,
        request=payload,
    )
    return recommendation_service.format_direct_recommendation(context)
