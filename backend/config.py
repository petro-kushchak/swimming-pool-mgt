from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    pools_config: str = Field(default="/data/pools.json", description="Path to pools configuration file")
    scheduler_interval: int = Field(default=60, ge=1, description="Scheduler check interval in seconds")
    api_port: int = Field(default=8083, ge=1, le=65535, description="API server port")
    build_version: str = Field(default="unknown", description="Build version string")
    version_file: str = Field(default="/app/VERSION", description="Path to version file")
    debug: bool = Field(default=False, description="Enable debug mode")
    api_key: str = Field(default="", description="API key for authentication")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def require_api_key() -> str:
    if not settings.api_key:
        raise RuntimeError("API_KEY environment variable is required but not set")
    return settings.api_key
