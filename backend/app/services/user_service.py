"""
User service handling user registration, queries, and credential authentication.
Keeps core business logic decoupled from API route handlers.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.auth import UserLogin
from app.auth.security import get_password_hash, verify_password
from app.exceptions.base import AppException, AuthenticationException


class UserService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Query user by email address."""
        normalized_email = email.strip().lower()
        stmt = select(User).where(User.email == normalized_email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Query user by primary key ID."""
        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def register_user(cls, db: Session, user_in: UserCreate) -> User:
        """
        Register a new user after verifying that the email is unique.
        Hashes password securely before persistence.
        """
        existing_user = cls.get_by_email(db, user_in.email)
        if existing_user:
            raise AppException(
                message="An account with this email already exists.",
                status_code=400,
                error_code="EMAIL_ALREADY_EXISTS",
                details={"email": user_in.email},
            )

        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @classmethod
    def authenticate_user(cls, db: Session, credentials: UserLogin) -> User:
        """
        Validate email and password against stored hash.
        Raises AuthenticationException on mismatch or inactive account.
        """
        user = cls.get_by_email(db, credentials.email)
        if not user or not verify_password(credentials.password, user.password_hash):
            raise AuthenticationException("Incorrect email or password.")

        if not user.is_active:
            raise AuthenticationException("User account is inactive.")

        return user

    @classmethod
    def get_or_create_default_user(
        cls,
        db: Session,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> User:
        """
        Retrieves the primary active user for single-user mode or initializes a default owner user.
        """
        target_email = (email or "alex.nutrition@example.com").strip().lower()
        user = cls.get_by_email(db, target_email)
        if user and user.is_active:
            return user

        stmt = select(User).where(User.is_active == True).order_by(User.id.asc()).limit(1)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

        import secrets
        random_pw = secrets.token_urlsafe(32)
        hashed_password = get_password_hash(random_pw)
        new_user = User(
            name=name or "Alex Nutrition",
            email=target_email,
            password_hash=hashed_password,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user


user_service = UserService()
