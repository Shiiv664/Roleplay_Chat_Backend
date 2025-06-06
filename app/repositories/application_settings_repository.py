"""Repository implementation for ApplicationSettings model."""

from functools import lru_cache
from typing import Optional, Type

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application_settings import ApplicationSettings
from app.repositories.base_repository import BaseRepository


class ApplicationSettingsRepository(BaseRepository[ApplicationSettings]):
    """Repository for ApplicationSettings entity."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session)
        # Create a method-specific cache that's bound to this instance
        self._cached_get_settings = lru_cache(maxsize=1)(self._get_settings_impl)

    def _get_model_class(self) -> Type[ApplicationSettings]:
        """Return the SQLAlchemy model class.

        Returns:
            ApplicationSettings: The ApplicationSettings model class
        """
        return ApplicationSettings

    def _get_settings_impl(self) -> ApplicationSettings:
        """Internal implementation to get settings, to be cached.

        Returns:
            ApplicationSettings: The application settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Use the model's get_instance method which handles the singleton pattern
            return ApplicationSettings.get_instance(self.session)
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving application settings")

    def get_settings(self) -> ApplicationSettings:
        """Get the application settings (singleton).

        This method uses caching for better performance.

        Returns:
            ApplicationSettings: The application settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        return self._cached_get_settings()

    def save_settings(self, **kwargs) -> ApplicationSettings:
        """Save application settings, creating or updating as needed.

        Args:
            **kwargs: Settings attributes to update

        Returns:
            ApplicationSettings: The updated settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            settings = self.get_settings()

            # Update existing settings
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            self.session.commit()

            # Invalidate cache
            self._cached_get_settings.cache_clear()

            return settings
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, "Error saving application settings")

    def update_default_ai_model(self, model_id: Optional[int]) -> ApplicationSettings:
        """Update the default AI model.

        Args:
            model_id: ID of the AI model to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        return self.save_settings(default_ai_model_id=model_id)

    def update_default_system_prompt(
        self, prompt_id: Optional[int]
    ) -> ApplicationSettings:
        """Update the default system prompt.

        Args:
            prompt_id: ID of the system prompt to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        return self.save_settings(default_system_prompt_id=prompt_id)

    def update_default_user_profile(
        self, profile_id: Optional[int]
    ) -> ApplicationSettings:
        """Update the default user profile.

        Args:
            profile_id: ID of the user profile to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        return self.save_settings(default_user_profile_id=profile_id)

    def update_default_avatar_image(
        self, avatar_path: Optional[str]
    ) -> ApplicationSettings:
        """Update the default avatar image path.

        Args:
            avatar_path: Path or URL to default avatar image, or None to clear

        Returns:
            ApplicationSettings: The updated settings instance

        Raises:
            DatabaseError: If a database error occurs
        """
        return self.save_settings(default_avatar_image=avatar_path)
