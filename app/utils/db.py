"""Database utilities for SQLAlchemy session management."""

from contextlib import contextmanager
from typing import Generator

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_config

# Create SQLAlchemy engine
config = get_config()
engine: Engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(app: Flask) -> None:
    """Initialize the database with Flask application.

    Args:
        app: Flask application instance
    """
    # Import models module to ensure models are registered
    import app.models  # noqa

    # Add teardown to ensure sessions are cleaned up
    app.teardown_appcontext(lambda _: None)  # Just a placeholder for now


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Yields:
        Session: SQLAlchemy session for database operations.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    """Get a new database session.

    This function is primarily for use in dependency injection.

    Returns:
        Session: SQLAlchemy session for database operations.
    """
    return SessionLocal()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session within a context manager.

    This function is used in API endpoints to ensure proper
    session management and transaction handling.

    Yields:
        Session: SQLAlchemy session for database operations.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
