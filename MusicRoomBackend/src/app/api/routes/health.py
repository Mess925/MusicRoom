from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.db.session import get_session

router = APIRouter(tags=["health"])

Status = Literal["ok", "error"]

_OK_EXAMPLE = {
    "status": "ok",
    "service": "Music Room API",
    "version": "0.1.0",
    "environment": "development",
    "database": "ok",
    "redis": "ok",
}
_DEGRADED_EXAMPLE = {**_OK_EXAMPLE, "status": "error", "redis": "error"}


class HealthResponse(BaseModel):
    """Roll-up of the service and each backing dependency."""

    model_config = {"json_schema_extra": {"examples": [_OK_EXAMPLE]}}

    status: Status = Field(description="`ok` only when every dependency is reachable.")
    service: str = Field(description="Human-readable service name.")
    version: str = Field(description="API version.")
    environment: str = Field(description="Deployment environment, e.g. `development`.")
    database: Status = Field(description="Result of `SELECT 1` against PostgreSQL.")
    redis: Status = Field(description="Result of `PING` against Redis.")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Verifies the API can reach PostgreSQL (`SELECT 1`) and Redis (`PING`).\n\n"
        "Returns **200** when both succeed and **503** otherwise, with the failing "
        "component marked `error`. Safe to poll — it opens no transactions and "
        "writes nothing."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Service and all dependencies healthy.",
            "content": {"application/json": {"example": _OK_EXAMPLE}},
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "At least one dependency is unreachable.",
            "model": HealthResponse,
            "content": {"application/json": {"example": _DEGRADED_EXAMPLE}},
        },
    },
)
async def health(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> HealthResponse:
    """Liveness + dependency readiness check."""
    database: Status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    cache: Status = "ok"
    try:
        await redis.ping()
    except Exception:
        cache = "error"

    healthy = database == "ok" and cache == "ok"
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if healthy else "error",
        service=settings.app_name,
        version=settings.api_version,
        environment=settings.environment,
        database=database,
        redis=cache,
    )
