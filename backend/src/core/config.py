import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/app_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept both JSON array and comma-separated string from env vars."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

settings = Settings()

def get_async_database_url() -> str:
    """Convert standard postgresql:// URL to async postgresql+asyncpg:// driver.

    Single source of truth — used by both database.py and alembic/env.py.
    Assumes the URL starts with "postgresql://". Will silently fail for
    "postgres://" (Heroku-style) or "postgresql+psycopg2://". If you need
    to support other schemes, use sqlalchemy.engine.make_url() instead.
    """
    return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
