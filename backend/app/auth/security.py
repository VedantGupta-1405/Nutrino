"""
Cryptographic security utilities for password hashing and JWT token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import jwt
from passlib.context import CryptContext
from app.config.settings import settings
from app.exceptions.base import AuthenticationException
from app.schemas.auth import TokenPayload

# Password hashing context using standard bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash for a plain password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate a signed JWT access token containing subject (user_id), issued-at, and expiration claims.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT access token.
    Raises AuthenticationException on expiration or invalid signature.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Token payload missing subject identifier")
        return TokenPayload(
            sub=user_id,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Authentication token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationException("Invalid authentication token")
