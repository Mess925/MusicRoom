from fastapi import APIRouter

from app.api.routes import health, room

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(room.router)
