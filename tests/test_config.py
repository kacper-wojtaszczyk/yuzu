"""Test configuration module."""

from yuzu.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Test that settings load with expected defaults."""
    settings = Settings()

    assert settings.environment == "development"
    assert settings.debug is True
    assert settings.postgres_user == "yuzu"
    assert settings.postgres_db == "yuzu"


def test_database_url_construction() -> None:
    """Test database URL is constructed correctly."""
    settings = Settings(
        postgres_user="test_user",
        postgres_password="test_pass",
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
    )

    url = settings.database_url
    assert "postgresql+psycopg://" in url
    assert "test_user" in url
    assert "test_pass" in url
    assert "test_db" in url


def test_get_settings_caching() -> None:
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
