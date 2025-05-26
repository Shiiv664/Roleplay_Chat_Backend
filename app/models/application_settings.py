"""ApplicationSettings model for the application.

This module defines the ApplicationSettings model representing global application
settings. It is designed as a singleton table with only one row.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ApplicationSettings(Base):
    """ApplicationSettings model for global application configuration.

    This is a singleton table with only one row.

    Attributes:
        id: Primary key, always set to 1.
        default_ai_model_id: Foreign key to the default AI model.
        default_system_prompt_id: Foreign key to the default system prompt.
        default_user_profile_id: Foreign key to the default user profile.
        default_avatar_image: Path or URL to default avatar image.
        openrouter_api_key_encrypted: Encrypted OpenRouter API key for AI model access.
    """

    __tablename__ = "applicationSettings"
    __table_args__ = (CheckConstraint("id = 1", name="application_settings_singleton"),)

    id: Mapped[int] = Column(Integer, primary_key=True, default=1)
    default_ai_model_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("aiModel.id"), nullable=True
    )
    default_system_prompt_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("systemPrompt.id"), nullable=True
    )
    default_user_profile_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("userProfile.id"), nullable=True
    )
    default_avatar_image: Mapped[Optional[str]] = Column(String, nullable=True)
    openrouter_api_key_encrypted: Mapped[Optional[str]] = Column(String, nullable=True)
    default_formatting_rules: Mapped[Optional[str]] = Column(Text, nullable=True)

    # Relationships
    default_ai_model = relationship("AIModel", back_populates="default_in_settings")
    default_system_prompt = relationship(
        "SystemPrompt", back_populates="default_in_settings"
    )
    default_user_profile = relationship(
        "UserProfile", back_populates="default_in_settings"
    )

    @classmethod
    def get_instance(cls, session: "Session") -> "ApplicationSettings":
        """Get the singleton instance of ApplicationSettings.

        Creates a new instance if one doesn't exist.

        Args:
            session: SQLAlchemy session.

        Returns:
            The ApplicationSettings instance.
        """
        instance = session.query(cls).first()
        if instance is None:
            instance = cls(id=1)
            session.add(instance)
            session.flush()
        return instance

    def __repr__(self) -> str:
        """Return string representation of the application settings.

        Returns:
            String representation.
        """
        return "<ApplicationSettings(id=1)>"
