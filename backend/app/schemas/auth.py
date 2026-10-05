"""
Pydantic schemas for authentication credentials, tokens, and token payloads.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.user import UserResponse


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class Token(BaseModel):
    """Schema for JWT access token response."""
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserResponse = Field(..., description="Authenticated user summary")


class TokenPayload(BaseModel):
    """Internal schema for decoded JWT payload."""
    sub: str = Field(..., description="Subject claim containing the user ID")
    exp: int = Field(..., description="Expiration timestamp (Unix timestamp)")
    iat: Optional[int] = Field(None, description="Issued-at timestamp (Unix timestamp)")
