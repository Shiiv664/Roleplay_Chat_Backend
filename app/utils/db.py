"""Database utilities for SQLAlchemy session management."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_config

# Create SQLAlchemy engine
config = get_config()
engine: Engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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