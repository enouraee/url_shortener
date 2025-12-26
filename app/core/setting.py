from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "settings"]

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class EnvSettingsOptions(Enum):
    production = "production"
    staging = "staging"
    development = "dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # Project Configuration
    ENV_SETTING: EnvSettingsOptions = Field(
        "production", examples=["production", "staging", "dev"]
    )
    # asyncpg DSN, URL-encode special chars in password
    PG_DSN: str | None = Field(default=None)
    
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_PRE_PING: bool = Field(default=True)
    DB_POOL_RECYCLE: int = Field(default=3600)
    DB_ECHO: bool = Field(default=False)


settings = Settings()
