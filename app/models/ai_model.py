"""AI Model model for the application.

This module defines the AIModel model representing different AI models
that can be used in roleplay chat sessions.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base


class AIModel(Base):
    """AI Model for roleplay chat sessions.

    Attributes:
        id: Unique identifier for the AI model.
        label: Unique label used to identify the AI model in the system.
        description: Detailed description of the AI model.
        created_at: When the AI model was created.
    """

    __tablename__ = "aiModel"

    id: Mapped[int] = Column(Integer, primary_key=True)
    label: Mapped[str] = Column(String, nullable=False, unique=True)
    description: Mapped[str] = Column(Text, nullable=True)
    created_at: Mapped[DateTime] = Column(
        DateTime, default=func.current_timestamp(), nullable=False
    )

    # Relationships - we'll define these properly when implementing ChatSession
    chat_sessions = relationship(
        "ChatSession",
        back_populates="ai_model",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # For application settings relationship
    default_in_settings = relationship(
        "ApplicationSettings",
        back_populates="default_ai_model",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Return string representation of the AI model.

        Returns:
            String representation.
        """
        return f"<AIModel(id={self.id}, label='{self.label}')>"
