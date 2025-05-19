"""Base SQLAlchemy model and declarative base configuration."""
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Common methods for all models
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Base":
        """Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model attributes.

        Returns:
            Base: New model instance.
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__table__.columns.keys()})


@declarative_mixin
class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Creation timestamp for the record.

        Returns:
            Column: SQLAlchemy Column with default value set to current timestamp.
        """
        return Column(DateTime, default=func.current_timestamp(), nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """Last update timestamp for the record.

        Returns:
            Column: SQLAlchemy Column with default value and onupdate set to current timestamp.
        """
        return Column(
            DateTime,
            default=func.current_timestamp(),
            onupdate=func.current_timestamp(),
            nullable=False,
        )