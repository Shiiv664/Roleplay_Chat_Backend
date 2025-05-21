"""User Profile model for the application.

This module defines the UserProfile model representing user profiles
that can be used in roleplay chat sessions.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """User Profile model for roleplay chat sessions.

    Attributes:
        id: Unique identifier for the user profile.
        label: Unique label used to identify the user profile in the system.
        name: Display name of the user profile.
        avatar_image: Path or URL to user's avatar image.
        description: Detailed description of the user profile.
        created_at: When the user profile was created.
        updated_at: When the user profile was last updated.
    """

    __tablename__ = "userProfile"

    id: Mapped[int] = Column(Integer, primary_key=True)
    label: Mapped[str] = Column(String, nullable=False, unique=True)
    name: Mapped[str] = Column(String, nullable=False)
    avatar_image: Mapped[str] = Column(String, nullable=True)
    description: Mapped[str] = Column(Text, nullable=True)

    # Relationships - we'll define these properly when implementing ChatSession
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user_profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # For application settings relationship
    default_in_settings = relationship(
        "ApplicationSettings",
        back_populates="default_user_profile",
        uselist=False,
    )

    def get_avatar_url(self) -> str:
        """Get the avatar URL for this user profile.

        Returns:
            str: The avatar URL or None if no avatar is set
        """
        from app.services.file_upload_service import FileUploadService

        file_service = FileUploadService()
        return file_service.get_avatar_url(self.avatar_image)

    def __repr__(self) -> str:
        """Return string representation of the user profile.

        Returns:
            String representation.
        """
        return f"<UserProfile(id={self.id}, label='{self.label}', name='{self.name}')>"
