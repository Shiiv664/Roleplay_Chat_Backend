"""System Prompt model for the application.

This module defines the SystemPrompt model representing system prompts
that can be used in roleplay chat sessions.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base


class SystemPrompt(Base):
    """System Prompt model for roleplay chat sessions.

    Attributes:
        id: Unique identifier for the system prompt.
        label: Unique label used to identify the system prompt in the system.
        content: The actual prompt text content.
        created_at: When the system prompt was created.
    """

    __tablename__ = "systemPrompt"

    id: Mapped[int] = Column(Integer, primary_key=True)
    label: Mapped[str] = Column(String, nullable=False, unique=True)
    content: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[DateTime] = Column(
        DateTime, default=func.current_timestamp(), nullable=False
    )

    # Relationships - we'll define these properly when implementing ChatSession
    chat_sessions = relationship(
        "ChatSession",
        back_populates="system_prompt",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # For application settings relationship
    default_in_settings = relationship(
        "ApplicationSettings",
        back_populates="default_system_prompt",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Return string representation of the system prompt.

        Returns:
            String representation.
        """
        return f"<SystemPrompt(id={self.id}, label='{self.label}')>"
