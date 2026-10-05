"""
FastAPI authentication dependencies for token extraction and current-user resolution.
"""

from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.services.user_service import user_service
from app.auth.security import decode_access_token
from app.exceptions.base import AuthenticationException

# HTTPBearer scheme that does not raise default Starlette HTTPException so our AppException handler handles it
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts Bearer token from the Authorization header, validates claims,
    and returns the authenticated User entity from the database.
    """
    if auth_credentials is None or not auth_credentials.credentials:
        raise AuthenticationException("Missing or invalid Authorization header.")

    token = auth_credentials.credentials
    payload = decode_access_token(token)

    try:
        user_id = int(payload.sub)
    except (ValueError, TypeError):
        raise AuthenticationException("Invalid token subject format.")

    user = user_service.get_by_id(db, user_id=user_id)
    if user is None:
        raise AuthenticationException("User belonging to this token no longer exists.")

    if not user.is_active:
        raise AuthenticationException("User account is inactive.")

    return user
