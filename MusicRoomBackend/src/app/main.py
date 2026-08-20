from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core import openapi
from app.core.config import settings
from app.core.redis import pool
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()
    await pool.aclose()


docs_on = settings.docs_enabled

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    summary="Music Room platform API — authoritative state for all clients.",
    description=openapi.DESCRIPTION,
    openapi_tags=openapi.TAGS_METADATA,
    contact=openapi.CONTACT,
    license_info=openapi.LICENSE_INFO,
    servers=openapi.SERVERS,
    swagger_ui_parameters=openapi.SWAGGER_UI_PARAMETERS,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=settings.docs_url if docs_on else None,
    redoc_url=settings.redoc_url if docs_on else None,
    openapi_url=settings.openapi_url if docs_on else None,
)

app.include_router(api_router)


@app.get(
    "/",
    tags=["root"],
    summary="Service banner",
    description="Identifies the service and points at the interactive API reference.",
)
async def root() -> dict[str, str | None]:
    return {
        "service": settings.app_name,
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": settings.docs_url if docs_on else None,
        "redoc": settings.redoc_url if docs_on else None,
        "openapi": settings.openapi_url if docs_on else None,
    }
