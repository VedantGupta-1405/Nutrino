"""
Nutrition goal management endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.goal import GoalUpdate, GoalResponse
from app.services.goal_service import goal_service
from app.exceptions.base import ResourceNotFoundException

router = APIRouter()


@router.get(
    "",
    response_model=GoalResponse,
    summary="Get authenticated user's active goal",
    description="Retrieves the current primary nutrition goal and macro targets for the authenticated user.",
)
def get_user_goal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    goal = goal_service.get_by_user_id(db, current_user.id)
    if goal is None:
        raise ResourceNotFoundException("Goal", current_user.id)
    return GoalResponse.model_validate(goal)


@router.put(
    "",
    response_model=GoalResponse,
    summary="Create or update user goal",
    description="Idempotently creates or updates the active nutrition goal and target macros for the authenticated user.",
)
def update_user_goal(
    goal_in: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    goal = goal_service.upsert_goal(
        db=db,
        user_id=current_user.id,
        goal_in=goal_in,
    )
    return GoalResponse.model_validate(goal)
