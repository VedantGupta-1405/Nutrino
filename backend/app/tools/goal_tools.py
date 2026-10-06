"""
Controlled goal tools for the agent layer.
Retrieves active target calories, macronutrient split, and health objectives.
User identity is derived strictly from the authenticated backend context.
"""

from app.exceptions.base import ResourceNotFoundException
from app.schemas.goal import GoalResponse
from app.services.goal_service import goal_service
from app.tools.base import BaseTool, EmptyInput, ToolContext


class GetActiveGoalTool(BaseTool[EmptyInput, GoalResponse]):
    """Tool for retrieving the authenticated user's active nutrition goal."""

    name = "get_active_goal"
    description = (
        "Retrieve the authenticated user's active nutrition goal and daily targets, "
        "including target calories, protein, carbohydrates, and fat."
    )
    input_schema = EmptyInput
    output_schema = GoalResponse
    requires_auth = True

    def execute(self, params: EmptyInput, context: ToolContext) -> GoalResponse:
        user_id = context.user_id
        goal = goal_service.get_by_user_id(db=context.db, user_id=user_id)
        if goal is None:
            raise ResourceNotFoundException("Goal", user_id)
        return GoalResponse.model_validate(goal)
