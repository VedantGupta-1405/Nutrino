"""
UserProfile model for persistent user nutritional and dietary context.
"""

from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """
    Stores persistent nutritional context, physical metrics, preferences, and constraints.
    Associated one-to-one with User.
    
    Lists (preferred cuisines, allergies, disliked foods, available ingredients)
    are stored using native JSON for clean array serialization, query flexibility,
    and avoiding arbitrary delimiter issues.
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in centimeters
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in kilograms
    activity_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dietary_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Structured list fields stored as JSON arrays
    preferred_cuisine: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    allergies_or_restrictions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    disliked_foods: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    budget_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in user's currency
    available_ingredients: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} diet={self.dietary_preference}>"
