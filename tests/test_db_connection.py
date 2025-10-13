"""Test database connection functionality."""

from sqlalchemy import text

from yuzu.pipeline.db.connection import get_db_session, test_connection


def test_database_connection() -> None:
    """Test that database connection works."""
    assert test_connection() is True


def test_session_context_manager() -> None:
    """Test that session context manager works correctly."""
    with get_db_session() as session:
        result = session.execute(text("SELECT 42 as answer")).scalar()
        assert result == 42


def test_postgis_available() -> None:
    """Test that PostGIS extension is available."""
    with get_db_session() as session:
        # Query PostGIS version
        version = session.execute(text("SELECT PostGIS_Version()")).scalar()
        assert version is not None
        assert "3.4" in version


def test_forest_schema_exists() -> None:
    """Test that forest schema was created."""
    with get_db_session() as session:
        result = session.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'forest'")
        ).scalar()
        assert result == "forest"
