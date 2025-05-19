"""ChatSession model for the application.

This module defines the ChatSession model representing a roleplay chat session
between a user profile and a character, using a specific AI model and system prompt.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base


class ChatSession(Base):
    """ChatSession model for roleplay chat interactions.

    Attributes:
        id: Unique identifier for the chat session.
        start_time: When the chat session was started.
        updated_at: When the chat session was last updated.
        character_id: Foreign key to the character in this chat.
        user_profile_id: Foreign key to the user profile in this chat.
        ai_model_id: Foreign key to the AI model used in this chat.
        system_prompt_id: Foreign key to the system prompt used in this chat.
        pre_prompt: Optional text added before each message to the AI.
        pre_prompt_enabled: Whether the pre-prompt is enabled.
        post_prompt: Optional text added after each message to the AI.
        post_prompt_enabled: Whether the post-prompt is enabled.
    """

    __tablename__ = "chatSession"

    id: Mapped[int] = Column(Integer, primary_key=True)
    start_time: Mapped[datetime] = Column(
        DateTime, default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    # Foreign keys
    character_id: Mapped[int] = Column(
        Integer, ForeignKey("character.id", ondelete="CASCADE"), nullable=False
    )
    user_profile_id: Mapped[int] = Column(
        Integer, ForeignKey("userProfile.id", ondelete="SET NULL"), nullable=False
    )
    ai_model_id: Mapped[int] = Column(
        Integer, ForeignKey("aiModel.id", ondelete="SET NULL"), nullable=False
    )
    system_prompt_id: Mapped[int] = Column(
        Integer, ForeignKey("systemPrompt.id", ondelete="SET NULL"), nullable=False
    )

    # Additional fields
    pre_prompt: Mapped[Optional[str]] = Column(Text, nullable=True)
    pre_prompt_enabled: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    post_prompt: Mapped[Optional[str]] = Column(Text, nullable=True)
    post_prompt_enabled: Mapped[bool] = Column(Boolean, default=False, nullable=False)

    # Relationships
    character = relationship("Character", back_populates="chat_sessions")
    user_profile = relationship("UserProfile", back_populates="chat_sessions")
    ai_model = relationship("AIModel", back_populates="chat_sessions")
    system_prompt = relationship("SystemPrompt", back_populates="chat_sessions")
    messages = relationship(
        "Message",
        back_populates="chat_session",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """Return string representation of the chat session.

        Returns:
            String representation.
        """
        return (
            f"<ChatSession(id={self.id}, character_id={self.character_id}, "
            f"user_profile_id={self.user_profile_id})>"
        )
