"""
FoodItem model representing normalized nutritional values and serving definitions.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy import CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class FoodItem(Base, TimestampMixin):
    """
    Authoritative food and nutrition record.
    Nutritional values are stored as PostgreSQL NUMERIC(8, 2) to preserve exact decimal precision
    rather than imprecise floating-point numbers.
    """

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="OTHER")

    # Serving basis
    serving_size: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    serving_unit: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'gram', 'piece', 'ml', 'cup'

    # Macronutrient & energy values per serving_size
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)       # in grams
    carbohydrates: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False) # in grams
    fat: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)           # in grams
    fiber: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=Decimal("0.00")) # in grams

    # Provenance
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="INTERNAL_DEV_DATASET")

    __table_args__ = (
        CheckConstraint("serving_size > 0", name="chk_food_serving_size_positive"),
        CheckConstraint("calories >= 0", name="chk_food_calories_non_negative"),
        CheckConstraint("protein >= 0", name="chk_food_protein_non_negative"),
        CheckConstraint("carbohydrates >= 0", name="chk_food_carbohydrates_non_negative"),
        CheckConstraint("fat >= 0", name="chk_food_fat_non_negative"),
        CheckConstraint("fiber >= 0", name="chk_food_fiber_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<FoodItem id={self.id} name='{self.name}' ({self.serving_size} {self.serving_unit})>"
