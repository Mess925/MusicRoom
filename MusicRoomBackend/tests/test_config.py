"""Settings: defaults, env parsing and caching."""

from app.core.config import Settings, get_settings, settings


def test_env_pinned_by_conftest_wins_over_dotenv() -> None:
    assert settings.environment == "test"
    assert settings.api_version == "9.9.9"
    assert settings.debug is False


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
    assert get_settings() is settings


def test_urls_are_validated_dsns() -> None:
    parsed = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@db:5432/app",
        REDIS_URL="redis://cache:6379/3",
    )

    assert parsed.database_url.scheme == "postgresql+asyncpg"
    assert parsed.database_url.hosts()[0]["host"] == "db"
    assert parsed.database_url.hosts()[0]["port"] == 5432
    assert parsed.database_url.path == "/app"
    assert parsed.redis_url.host == "cache"
    assert parsed.redis_url.path == "/3"


def test_pool_and_docs_defaults() -> None:
    fresh = Settings(_env_file=None)

    assert fresh.db_pool_size == 5
    assert fresh.db_max_overflow == 10
    assert fresh.db_echo is False
    assert fresh.docs_url == "/docs"
    assert fresh.redoc_url == "/redoc"
    assert fresh.openapi_url == "/openapi.json"


def test_unknown_env_vars_are_ignored() -> None:
    """extra="ignore" — an unrelated variable must not blow up startup."""
    assert Settings(SOME_UNRELATED_VAR="x").app_name == "Music Room API Test"
