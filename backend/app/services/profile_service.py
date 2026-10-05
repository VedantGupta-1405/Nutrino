"""
Service layer for UserProfile operations.
Decouples database access and domain logic from API route handlers.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.profile import UserProfile
from app.schemas.profile import UserProfileUpdate


class ProfileService:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[UserProfile]:
        """Fetch profile for a specific user."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def upsert_profile(
        cls,
        db: Session,
        user_id: int,
        profile_in: UserProfileUpdate,
    ) -> UserProfile:
        """
        Create or update user profile idempotently.
        Ensures strict 1-to-1 association with User.
        """
        profile = cls.get_by_user_id(db, user_id)
        update_data = profile_in.model_dump(exclude_unset=True)

        if profile is None:
            profile = UserProfile(user_id=user_id, **update_data)
            db.add(profile)
        else:
            for field, value in update_data.items():
                setattr(profile, field, value)

        db.commit()
        db.refresh(profile)
        return profile


profile_service = ProfileService()
