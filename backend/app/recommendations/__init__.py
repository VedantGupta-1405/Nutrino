"""
Recommendations package for personalized, constraint-driven meal suggestions.
"""

from app.recommendations.schemas import (
    FoodCandidate,
    RecommendationContext,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.recommendations.service import recommendation_service, RecommendationService

__all__ = [
    "FoodCandidate",
    "RecommendationContext",
    "RecommendationItem",
    "RecommendationRequest",
    "RecommendationResponse",
    "recommendation_service",
    "RecommendationService",
]
