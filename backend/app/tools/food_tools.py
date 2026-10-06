"""
Controlled food catalog tools for the agent layer.
These tools are read-only interfaces to the existing FoodService.
"""

from app.exceptions.base import ResourceNotFoundException
from app.schemas.food import FoodItemResponse
from app.services.food_service import food_service
from app.tools.base import BaseTool, ToolContext
from app.tools.schemas import (
    FoodSummaryItem,
    GetFoodInput,
    SearchFoodsInput,
    SearchFoodsOutput,
)


class SearchFoodTool(BaseTool[SearchFoodsInput, SearchFoodsOutput]):
    """Tool for searching items in the nutrition food catalog."""

    name = "search_foods"
    description = (
        "Search the authoritative food catalog by name or keyword. "
        "Returns matching food items with their catalog IDs, serving units, and categories."
    )
    input_schema = SearchFoodsInput
    output_schema = SearchFoodsOutput
    requires_auth = False

    def execute(self, params: SearchFoodsInput, context: ToolContext) -> SearchFoodsOutput:
        items = food_service.search(
            db=context.db,
            query=params.query,
            category=params.category,
            limit=params.limit,
        )
        summaries = [
            FoodSummaryItem(
                id=item.id,
                name=item.name,
                category=item.category,
                serving_size=item.serving_size,
                serving_unit=item.serving_unit,
                source=item.source,
            )
            for item in items
        ]
        return SearchFoodsOutput(foods=summaries, count=len(summaries))


class GetFoodTool(BaseTool[GetFoodInput, FoodItemResponse]):
    """Tool for retrieving detailed nutrition data for a single catalog food item."""

    name = "get_food"
    description = (
        "Retrieve complete nutritional facts, serving sizes, and macro profiles "
        "for a specific food item from the catalog by its ID."
    )
    input_schema = GetFoodInput
    output_schema = FoodItemResponse
    requires_auth = False

    def execute(self, params: GetFoodInput, context: ToolContext) -> FoodItemResponse:
        food = food_service.get_by_id(db=context.db, food_id=params.food_id)
        if food is None:
            raise ResourceNotFoundException("FoodItem", params.food_id)
        return FoodItemResponse.model_validate(food)
