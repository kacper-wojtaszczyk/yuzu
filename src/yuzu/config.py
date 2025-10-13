"""Configuration management for Yuzu.

Uses Pydantic Settings for type-safe environment variable loading.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=True, description="Enable debug mode")

    # Project paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent,
        description="Root directory of the project",
    )

    # Database
    postgres_user: str = Field(default="yuzu", description="PostgreSQL username")
    postgres_password: str = Field(default="yuzu_dev_password", description="PostgreSQL password")
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="yuzu", description="PostgreSQL database name")

    @property
    def database_url(self) -> str:
        """Construct the database connection URL."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    # Data directories
    @property
    def data_dir(self) -> Path:
        """Root data directory."""
        return self.project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        """Raw data storage."""
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Processed data storage."""
        return self.data_dir / "processed"

    # LLM Configuration (to be expanded)
    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    llm_api_key: str | None = Field(default=None, description="LLM API key")
    llm_model: str = Field(default="gpt-4", description="LLM model name")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application configuration.
    """
    return Settings()
