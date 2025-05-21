"""Character model for the application.

This module defines the Character model representing fictional characters
that can be used in roleplay chat sessions.
"""

from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession


class Character(Base, TimestampMixin):
    """Character model for roleplay chat sessions.

    Attributes:
        id: Unique identifier for the character.
        label: Unique label used to identify the character in the system.
        name: Display name of the character.
        avatar_image: Path or URL to character's avatar image.
        description: Detailed description of the character.
        created_at: When the character was created.
        updated_at: When the character was last updated.
    """

    __tablename__ = "character"

    id: Mapped[int] = Column(Integer, primary_key=True)
    label: Mapped[str] = Column(String, nullable=False, unique=True)
    name: Mapped[str] = Column(String, nullable=False)
    avatar_image: Mapped[str] = Column(String, nullable=True)
    description: Mapped[str] = Column(Text, nullable=True)

    # Relationships
    chat_sessions: "Mapped[List['ChatSession']]" = relationship(
        "ChatSession",
        back_populates="character",
        cascade="all, delete-orphan",
        lazy="dynamic",
        uselist=True,
    )

    def get_avatar_url(self) -> str:
        """Get the avatar URL for this character.

        Returns:
            str: The avatar URL or None if no avatar is set
        """
        from app.services.file_upload_service import FileUploadService

        file_service = FileUploadService()
        return file_service.get_avatar_url(self.avatar_image)

    def __repr__(self) -> str:
        """Return string representation of the character.

        Returns:
            String representation.
        """
        return f"<Character(id={self.id}, label='{self.label}', name='{self.name}')>"
