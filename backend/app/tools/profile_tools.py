"""
Controlled user profile tools for the agent layer.
Retrieves user dietary preferences, restrictions, and health context.
User identity is derived strictly from the authenticated backend context.
"""

from app.exceptions.base import ResourceNotFoundException
from app.schemas.profile import UserProfileResponse
from app.services.profile_service import profile_service
from app.tools.base import BaseTool, EmptyInput, ToolContext


class GetUserProfileTool(BaseTool[EmptyInput, UserProfileResponse]):
    """Tool for retrieving the authenticated user's dietary profile."""

    name = "get_user_profile"
    description = (
        "Retrieve the authenticated user's profile containing dietary preferences "
        "(vegetarian, vegan, etc.), allergies/restrictions, preferred cuisine, "
        "and physical metrics (weight, height, activity level)."
    )
    input_schema = EmptyInput
    output_schema = UserProfileResponse
    requires_auth = True

    def execute(self, params: EmptyInput, context: ToolContext) -> UserProfileResponse:
        user_id = context.user_id
        profile = profile_service.get_by_user_id(db=context.db, user_id=user_id)
        if profile is None:
            raise ResourceNotFoundException("UserProfile", user_id)
        return UserProfileResponse.model_validate(profile)
