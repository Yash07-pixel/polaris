"""Application settings for the MolGenix prototype."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    APP_NAME: str = "MolGenix"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = Field(default="sqlite:///./molgenix.db")
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlite_path(self) -> Path | None:
        """Return the local SQLite file path when DATABASE_URL uses sqlite."""

        prefix = "sqlite:///"
        if not self.DATABASE_URL.startswith(prefix):
            return None
        return Path(self.DATABASE_URL.removeprefix(prefix))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
