"""
Health check endpoints for system observability, liveness, and readiness.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, status, Response
from app.config.settings import settings
from app.database.session import check_db_connection
from app.schemas.health import HealthResponse, DatabaseHealth

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Comprehensive Health Check",
    description="Returns the current operational status of the backend API and PostgreSQL database.",
)
def get_health(response: Response) -> HealthResponse:
    db_status = check_db_connection()
    is_healthy = db_status.get("status") == "healthy"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        database=DatabaseHealth(
            status=db_status.get("status", "unknown"),
            database=db_status.get("database", "postgresql"),
            latency_ms=db_status.get("latency_ms"),
            error=db_status.get("error"),
        ),
    )


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Simple probe to check if the application process is running.",
)
def get_liveness() -> dict:
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Check whether the application and database dependencies are ready to accept traffic.",
)
def get_readiness(response: Response) -> dict:
    db_status = check_db_connection()
    if db_status.get("status") != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": db_status}
    return {"status": "ready", "database": "connected"}
