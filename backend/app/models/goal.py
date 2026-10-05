"""
Goal model for storing user nutrition targets and objectives.
"""

from typing import Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Goal(Base, TimestampMixin):
    """
    Represents the user's active nutrition goal and target macros.
    Associated with User.
    """

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)       # in grams
    target_carbohydrates: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # in grams
    target_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # in grams

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="goal")

    def __repr__(self) -> str:
        return f"<Goal user_id={self.user_id} type='{self.goal_type}'>"
