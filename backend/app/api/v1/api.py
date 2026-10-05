"""
API v1 Router aggregating all endpoint sub-routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, profile, goals, foods

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User Profile endpoints
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])

# Nutrition Goal endpoints
api_router.include_router(goals.router, prefix="/goals", tags=["Goals"])

# Food catalog endpoints
api_router.include_router(foods.router, prefix="/foods", tags=["Foods"])
