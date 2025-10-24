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

    # Google Earth Engine Configuration
    gee_project_id: str = Field(
        default="", description="Google Earth Engine project ID from Cloud Console"
    )
    gee_service_account_email: str | None = Field(
        default=None, description="GEE service account email (optional, for automation)"
    )
    gee_private_key_path: Path | None = Field(
        default=None, description="Path to GEE service account private key JSON (optional)"
    )

    # Hansen GFW Configuration
    hansen_dataset_version: str = Field(
        default="v1.12", description="Hansen GFW dataset version"
    )
    hansen_asset_id: str = Field(
        default="UMD/hansen/global_forest_change_2024_v1_12",
        description="Google Earth Engine asset ID for Hansen dataset",
    )
    tree_cover_threshold: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Minimum % canopy cover to classify as forest",
    )
    gee_scale_meters: int = Field(
        default=30, description="Processing scale in meters (Hansen native resolution)"
    )
    gee_max_pixels: int = Field(
        default=1_000_000_000, description="Maximum pixels per GEE request"
    )
    gee_request_timeout_sec: int = Field(
        default=300, description="GEE API request timeout in seconds"
    )
    gee_max_retries: int = Field(default=3, description="Maximum retry attempts for GEE requests")
    gee_backoff_factor: float = Field(
        default=2.0, description="Exponential backoff factor for retries"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application configuration.
    """
    return Settings()
