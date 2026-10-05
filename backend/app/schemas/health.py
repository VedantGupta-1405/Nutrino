"""
Pydantic schemas for health checks and system status.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    status: str = Field(..., description="Database connection status ('healthy' or 'unhealthy')")
    database: str = Field(default="postgresql", description="Database engine type")
    latency_ms: Optional[float] = Field(None, description="Round-trip query latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status ('healthy' or 'degraded')")
    environment: str = Field(..., description="Deployment environment (development, production, etc.)")
    version: str = Field(..., description="Current API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the check")
    database: DatabaseHealth = Field(..., description="Database connectivity information")
