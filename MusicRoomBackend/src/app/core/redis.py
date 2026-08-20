from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

pool = ConnectionPool.from_url(
    str(settings.redis_url),
    decode_responses=True,
    max_connections=10,
)


def get_redis_client() -> Redis:
    """Build a Redis client backed by the shared connection pool."""
    return Redis(connection_pool=pool)


async def get_redis() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency yielding a Redis client."""
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()
