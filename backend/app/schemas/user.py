"""
Pydantic schemas for User registration, response, and profile updates.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user properties shared across request/response schemas."""
    name: str = Field(..., min_length=1, max_length=100, description="Full name or display name")
    email: EmailStr = Field(..., description="Unique email address")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long",
    )


class UserResponse(UserBase):
    """Safe public schema for user information; never exposes password or sensitive hashes."""
    id: int = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Timestamp of account creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

    model_config = ConfigDict(from_attributes=True)
