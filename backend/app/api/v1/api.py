"""
API v1 Router aggregating all endpoint sub-routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
