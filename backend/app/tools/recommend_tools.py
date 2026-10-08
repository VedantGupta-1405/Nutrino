"""
Controlled recommendation tool for generating personalized meal suggestions.
Enforces authenticated user context, retrieves real user facts and database foods,
applies deterministic constraints, and returns structured recommendation candidates.
"""

from app.recommendations.schemas import RecommendationContext, RecommendationRequest
from app.recommendations.service import recommendation_service
from app.tools.base import BaseTool, ToolContext
from app.tools.schemas import RecommendMealInput


class RecommendMealTool(BaseTool[RecommendMealInput, RecommendationContext]):
    """Tool for obtaining personalized meal recommendations."""

    name = "recommend_meal"
    description = (
        "Generate personalized meal recommendations based on the authenticated user's "
        "profile (dietary preferences, allergies, disliked foods, available ingredients), "
        "active goal, today's remaining calories and macronutrients, and catalog foods. "
        "Accepts temporary request-specific constraints: ad_hoc_restrictions (e.g. ['paneer']), "
        "ad_hoc_dislikes (e.g. ['mushrooms']), and ad_hoc_dietary_preference (e.g. 'VEGETARIAN', 'VEGAN'). "
        "Strictly read-only: does NOT create or log meals."
    )
    input_schema = RecommendMealInput
    output_schema = RecommendationContext
    requires_auth = True

    def execute(self, params: RecommendMealInput, context: ToolContext) -> RecommendationContext:
        user = context.get_authenticated_user()
        request = RecommendationRequest(
            meal_type=params.meal_type,
            focus=params.focus,
            target_calories=params.target_calories,
            ingredients=params.ingredients,
            notes=params.notes,
            ad_hoc_restrictions=params.ad_hoc_restrictions,
            ad_hoc_dislikes=params.ad_hoc_dislikes,
            ad_hoc_dietary_preference=params.ad_hoc_dietary_preference,
        )
        return recommendation_service.build_recommendation_context(
            db=context.db,
            user=user,
            request=request,
        )
