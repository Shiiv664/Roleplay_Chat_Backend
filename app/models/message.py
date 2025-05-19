"""Message model for the application.

This module defines the Message model representing individual messages
exchanged in a chat session.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base


class MessageRole(Enum):
    """Enum for message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """Message model for roleplay chat interactions.

    Attributes:
        id: Unique identifier for the message.
        chat_session_id: Foreign key to the chat session this message belongs to.
        role: Whether this is a user or assistant (AI) message.
        content: The text content of the message.
        timestamp: When the message was created.
    """

    __tablename__ = "message"

    id: Mapped[int] = Column(Integer, primary_key=True)
    chat_session_id: Mapped[int] = Column(
        Integer, ForeignKey("chatSession.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = Column(SQLAlchemyEnum(MessageRole), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(
        DateTime, default=func.current_timestamp(), nullable=False
    )

    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        """Return string representation of the message.

        Returns:
            String representation.
        """
        return (
            f"<Message(id={self.id}, chat_session_id={self.chat_session_id}, "
            f"role={self.role.value})>"
        )
