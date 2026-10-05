"""
Pydantic schemas for UserProfile data validation, sanitization, and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActivityLevel(str, Enum):
    SEDENTARY = "SEDENTARY"
    LIGHTLY_ACTIVE = "LIGHTLY_ACTIVE"
    MODERATELY_ACTIVE = "MODERATELY_ACTIVE"
    VERY_ACTIVE = "VERY_ACTIVE"
    EXTRA_ACTIVE = "EXTRA_ACTIVE"


class DietaryPreference(str, Enum):
    VEGETARIAN = "VEGETARIAN"
    VEGAN = "VEGAN"
    NON_VEGETARIAN = "NON_VEGETARIAN"
    EGGETARIAN = "EGGETARIAN"
    PESCATARIAN = "PESCATARIAN"
    KETO = "KETO"
    PALEO = "PALEO"
    ANY = "ANY"


def _normalize_string_list(v: Optional[List[str]]) -> List[str]:
    """Helper to strip whitespace, filter blanks, and deduplicate list elements."""
    if not v:
        return []
    cleaned: list[str] = []
    seen = set()
    for item in v:
        if isinstance(item, str):
            clean_item = item.strip()
            if clean_item and clean_item.lower() not in seen:
                cleaned.append(clean_item)
                seen.add(clean_item.lower())
    return cleaned


class UserProfileBase(BaseModel):
    """Core user profile attributes for nutrition personalization."""

    age: Optional[int] = Field(None, ge=1, le=120, description="Age in years (1-120)")
    height: Optional[float] = Field(None, gt=0, le=300, description="Height in centimeters (e.g. 175.5)")
    weight: Optional[float] = Field(None, gt=0, le=500, description="Weight in kilograms (e.g. 70.2)")
    activity_level: Optional[str] = Field(None, description="Physical activity level")
    dietary_preference: Optional[str] = Field(None, description="Dietary pattern")

    preferred_cuisine: List[str] = Field(default_factory=list, description="List of preferred cuisines")
    allergies_or_restrictions: List[str] = Field(default_factory=list, description="Allergies and intolerances")
    disliked_foods: List[str] = Field(default_factory=list, description="Disliked foods to avoid")
    budget_per_day: Optional[float] = Field(None, ge=0, description="Estimated daily food budget")
    available_ingredients: List[str] = Field(default_factory=list, description="Currently available kitchen ingredients")

    @field_validator(
        "preferred_cuisine",
        "allergies_or_restrictions",
        "disliked_foods",
        "available_ingredients",
        mode="before",
    )
    @classmethod
    def sanitize_lists(cls, v):
        return _normalize_string_list(v)

    @field_validator("activity_level", mode="before")
    @classmethod
    def normalize_activity_level(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            val = v.strip().upper()
            return val if val else None
        return v

    @field_validator("dietary_preference", mode="before")
    @classmethod
    def normalize_dietary_preference(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            val = v.strip().upper()
            return val if val else None
        return v


class UserProfileCreate(UserProfileBase):
    """Schema for profile creation."""
    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for profile update/upsert."""
    pass


class UserProfileResponse(UserProfileBase):
    """Schema for serialized user profile output."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
