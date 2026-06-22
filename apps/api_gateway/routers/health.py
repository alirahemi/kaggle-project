"""Health check router."""

from fastapi import APIRouter

from apps.api_gateway.schemas.common import HealthResponse
from config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services={
            "api": "up",
            "app_env": settings.app_env,
            "database": "configured",
            "redis": "enabled" if settings.redis_enabled else "disabled",
        },
    )
