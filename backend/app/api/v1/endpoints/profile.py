"""
User profile management endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.profile import UserProfileUpdate, UserProfileResponse
from app.services.profile_service import profile_service
from app.exceptions.base import ResourceNotFoundException

router = APIRouter()


@router.get(
    "",
    response_model=UserProfileResponse,
    summary="Get authenticated user's profile",
    description="Retrieves persistent nutritional profile, preferences, and dietary restrictions for the current user.",
)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    profile = profile_service.get_by_user_id(db, current_user.id)
    if profile is None:
        raise ResourceNotFoundException("UserProfile", current_user.id)
    return UserProfileResponse.model_validate(profile)


@router.put(
    "",
    response_model=UserProfileResponse,
    summary="Create or update user profile",
    description="Idempotently creates or updates nutritional metrics, dietary preferences, and restrictions for the current user.",
)
def update_user_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    profile = profile_service.upsert_profile(
        db=db,
        user_id=current_user.id,
        profile_in=profile_in,
    )
    return UserProfileResponse.model_validate(profile)
