from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Music Room API"
    api_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Interactive API reference. Turn off in public deployments if the docs
    # should not be reachable.
    docs_enabled: bool = Field(default=True)
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://musicroom:musicroom@postgres:5432/musicroom"
    )
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)

    redis_url: RedisDsn = Field(default="redis://redis:6379/0")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
