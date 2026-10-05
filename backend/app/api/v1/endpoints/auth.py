"""
Authentication endpoints for user registration, login, and current identity resolution.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.config.settings import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin, Token
from app.services.user_service import user_service
from app.auth.security import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Validates unique email, hashes password securely, stores user, and returns access token.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Token:
    user = user_service.register_user(db=db, user_in=user_in)
    access_token = create_access_token(subject=user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and obtain JWT",
    description="Verifies user credentials and returns a signed JWT access token.",
)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = user_service.authenticate_user(db=db, credentials=credentials)
    access_token = create_access_token(subject=user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
    description="Resolves identity from validated Bearer JWT access token and returns safe user data.",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
