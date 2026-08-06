"""Centralised application configuration, sourced from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every value is overridable via the environment
    or a `.env` file — nothing here is a credential, only defaults for local
    development.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "POPIA Guard"

    # Database
    database_url: str = "postgresql+psycopg2://popia:popia@localhost:5432/popia_guard"

    # Auth
    jwt_secret_key: str = "changeme-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AWS / S3
    aws_region: str = "af-south-1"
    s3_bucket_name: str = "popia-guard-reports"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # CORS
    cors_allow_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is read once per process."""
    return Settings()
