"""
Meal and MealItem models for tracking logged foods, portion sizes, and historical nutrition snapshots.
"""

from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Meal(Base, TimestampMixin):
    """
    Represents an individual meal occasion (e.g. BREAKFAST, LUNCH) consumed by a user.
    """

    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # BREAKFAST, LUNCH, DINNER, SNACK, OTHER
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="meals")
    items: Mapped[List["MealItem"]] = relationship(
        "MealItem",
        back_populates="meal",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_meals_user_consumed", "user_id", "consumed_at"),
    )

    def __repr__(self) -> str:
        return f"<Meal id={self.id} user_id={self.user_id} type='{self.meal_type}' at={self.consumed_at}>"


class MealItem(Base, TimestampMixin):
    """
    Represents an individual food item within a meal.
    Stores an authoritative immutable snapshot of nutritional values calculated at the moment of logging.
    If the referenced FoodItem is updated in the catalog later, historical MealItem records remain unchanged.
    """

    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    meal_id: Mapped[int] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Historical nutrition snapshot
    calculated_calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calculated_protein: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calculated_carbohydrates: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calculated_fat: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calculated_fiber: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=Decimal("0.00"))

    # Relationships
    meal = relationship("Meal", back_populates="items")
    food_item = relationship("FoodItem", lazy="joined")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_meal_item_quantity_positive"),
        CheckConstraint("calculated_calories >= 0", name="chk_meal_item_calories_non_negative"),
        CheckConstraint("calculated_protein >= 0", name="chk_meal_item_protein_non_negative"),
        CheckConstraint("calculated_carbohydrates >= 0", name="chk_meal_item_carbs_non_negative"),
        CheckConstraint("calculated_fat >= 0", name="chk_meal_item_fat_non_negative"),
        CheckConstraint("calculated_fiber >= 0", name="chk_meal_item_fiber_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<MealItem id={self.id} meal_id={self.meal_id} food_id={self.food_item_id} ({self.quantity} {self.unit})>"
