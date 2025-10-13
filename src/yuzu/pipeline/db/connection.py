"""Database connection and session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from yuzu.config import get_settings


def get_engine() -> Engine:
    """Create SQLAlchemy engine with connection pooling."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.debug,  # Log SQL in debug mode
    )


def get_session_factory() -> sessionmaker[Session]:
    """Create a session factory."""
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Yields:
        Session: SQLAlchemy session.

    Example:
        ```python
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
        ```
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Test database connection and PostGIS availability.

    Returns:
        bool: True if connection successful and PostGIS is available.
    """
    try:
        with get_db_session() as session:
            # Test basic connection
            result = session.execute(text("SELECT 1 as test")).scalar()
            assert result == 1

            # Test PostGIS
            postgis_version = session.execute(text("SELECT PostGIS_Version()")).scalar()
            print(f"✅ Connected to PostgreSQL with PostGIS {postgis_version}")

            # Test forest schema
            schema_check = session.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'forest'"
                )
            ).scalar()
            assert schema_check == "forest"
            print("✅ Forest schema available")

            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
