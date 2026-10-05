"""
Pydantic schemas for Goal target validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoalType(str, Enum):
    WEIGHT_MANAGEMENT = "WEIGHT_MANAGEMENT"
    MUSCLE_GAIN = "MUSCLE_GAIN"
    GENERAL_HEALTH = "GENERAL_HEALTH"


SUPPORTED_GOAL_TYPES = {gt.value for gt in GoalType}


class GoalBase(BaseModel):
    """Core goal attributes for nutrition targets."""

    goal_type: str = Field(
        ...,
        description="Nutrition objective: WEIGHT_MANAGEMENT, MUSCLE_GAIN, or GENERAL_HEALTH",
    )
    target_calories: Optional[float] = Field(
        None,
        ge=0,
        le=10000,
        description="Target daily energy in kilocalories",
    )
    target_protein: Optional[float] = Field(
        None,
        ge=0,
        le=1000,
        description="Target daily protein in grams",
    )
    target_carbohydrates: Optional[float] = Field(
        None,
        ge=0,
        le=2000,
        description="Target daily carbohydrates in grams",
    )
    target_fat: Optional[float] = Field(
        None,
        ge=0,
        le=1000,
        description="Target daily fat in grams",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this goal is the user's active goal",
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes or context regarding this goal",
    )

    @field_validator("goal_type", mode="before")
    @classmethod
    def validate_goal_type(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().upper()
            if val not in SUPPORTED_GOAL_TYPES:
                supported = ", ".join(sorted(SUPPORTED_GOAL_TYPES))
                raise ValueError(
                    f"Invalid goal_type '{v}'. Must be one of: {supported}"
                )
            return val
        raise ValueError("goal_type must be a string")


class GoalCreate(GoalBase):
    """Schema for creating a goal."""
    pass


class GoalUpdate(BaseModel):
    """Schema for updating an existing goal (all fields optional)."""

    goal_type: Optional[str] = Field(
        None,
        description="Nutrition objective: WEIGHT_MANAGEMENT, MUSCLE_GAIN, or GENERAL_HEALTH",
    )
    target_calories: Optional[float] = Field(None, ge=0, le=10000)
    target_protein: Optional[float] = Field(None, ge=0, le=1000)
    target_carbohydrates: Optional[float] = Field(None, ge=0, le=2000)
    target_fat: Optional[float] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("goal_type", mode="before")
    @classmethod
    def validate_goal_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            val = v.strip().upper()
            if val not in SUPPORTED_GOAL_TYPES:
                supported = ", ".join(sorted(SUPPORTED_GOAL_TYPES))
                raise ValueError(
                    f"Invalid goal_type '{v}'. Must be one of: {supported}"
                )
            return val
        raise ValueError("goal_type must be a string")


class GoalResponse(GoalBase):
    """Schema for serialized goal output."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
