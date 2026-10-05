"""
Service layer for Goal operations.
Decouples database access and domain logic from API route handlers.
"""

from typing import Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate
from app.exceptions.base import ValidationException


class GoalService:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[Goal]:
        """Fetch the active goal for a specific user."""
        stmt = select(Goal).where(Goal.user_id == user_id, Goal.is_active.is_(True))
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def upsert_goal(
        cls,
        db: Session,
        user_id: int,
        goal_in: Union[GoalCreate, GoalUpdate],
    ) -> Goal:
        """
        Create or update the user's primary active goal.
        Guarantees user isolation and data integrity.
        """
        goal = cls.get_by_user_id(db, user_id)
        update_data = goal_in.model_dump(exclude_unset=True)

        if goal is None:
            if not update_data.get("goal_type"):
                raise ValidationException("goal_type is required when creating an initial goal.")
            goal = Goal(user_id=user_id, **update_data)
            db.add(goal)
        else:
            for field, value in update_data.items():
                setattr(goal, field, value)

        db.commit()
        db.refresh(goal)
        return goal


goal_service = GoalService()
