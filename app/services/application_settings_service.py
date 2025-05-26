"""Service for ApplicationSettings entity operations."""

import logging
from typing import Optional

from app.models.application_settings import ApplicationSettings
from app.repositories.ai_model_repository import AIModelRepository
from app.repositories.application_settings_repository import (
    ApplicationSettingsRepository,
)
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.utils.encryption import encryption_service
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ApplicationSettingsService:
    """Service for managing ApplicationSettings entity.

    This service implements business logic and validation for the ApplicationSettings
    entity, using the ApplicationSettingsRepository for data access along with repositories
    for related entities.
    """

    def __init__(
        self,
        application_settings_repository: ApplicationSettingsRepository,
        ai_model_repository: AIModelRepository,
        system_prompt_repository: SystemPromptRepository,
        user_profile_repository: UserProfileRepository,
    ):
        """Initialize the service with repositories.

        Args:
            application_settings_repository: Repository for ApplicationSettings data access
            ai_model_repository: Repository for AIModel data access
            system_prompt_repository: Repository for SystemPrompt data access
            user_profile_repository: Repository for UserProfile data access
        """
        self.repository = application_settings_repository
        self.ai_model_repository = ai_model_repository
        self.system_prompt_repository = system_prompt_repository
        self.user_profile_repository = user_profile_repository

    def get_settings(self) -> ApplicationSettings:
        """Get the application settings.

        This will return the singleton ApplicationSettings instance,
        creating it if it doesn't exist.

        Returns:
            ApplicationSettings: The application settings

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting application settings")
        return self.repository.get_settings()

    def update_default_ai_model(
        self, model_id: Optional[int] = None
    ) -> ApplicationSettings:
        """Update the default AI model.

        Args:
            model_id: ID of the AI model to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ResourceNotFoundError: If the AI model doesn't exist (when not None)
            DatabaseError: If a database error occurs
        """
        # Verify model exists if an ID is provided
        if model_id is not None:
            self.ai_model_repository.get_by_id(model_id)

        logger.info(f"Updating default AI model to {model_id if model_id else 'None'}")
        return self.repository.update_default_ai_model(model_id)

    def update_default_system_prompt(
        self, prompt_id: Optional[int] = None
    ) -> ApplicationSettings:
        """Update the default system prompt.

        Args:
            prompt_id: ID of the system prompt to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ResourceNotFoundError: If the system prompt doesn't exist (when not None)
            DatabaseError: If a database error occurs
        """
        # Verify prompt exists if an ID is provided
        if prompt_id is not None:
            self.system_prompt_repository.get_by_id(prompt_id)

        logger.info(
            f"Updating default system prompt to {prompt_id if prompt_id else 'None'}"
        )
        return self.repository.update_default_system_prompt(prompt_id)

    def update_default_user_profile(
        self, profile_id: Optional[int] = None
    ) -> ApplicationSettings:
        """Update the default user profile.

        Args:
            profile_id: ID of the user profile to set as default, or None to clear

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ResourceNotFoundError: If the user profile doesn't exist (when not None)
            DatabaseError: If a database error occurs
        """
        # Verify profile exists if an ID is provided
        if profile_id is not None:
            self.user_profile_repository.get_by_id(profile_id)

        logger.info(
            f"Updating default user profile to {profile_id if profile_id else 'None'}"
        )
        return self.repository.update_default_user_profile(profile_id)

    def update_default_avatar_image(
        self, avatar_path: Optional[str] = None
    ) -> ApplicationSettings:
        """Update the default avatar image path.

        Args:
            avatar_path: Path or URL to the default avatar image, or None to clear

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ValidationError: If the avatar path is invalid
            DatabaseError: If a database error occurs
        """
        # Validate avatar path if provided
        if avatar_path is not None and not avatar_path.strip():
            raise ValidationError(
                "Avatar path cannot be empty string",
                details={
                    "default_avatar_image": "Must provide a valid path or URL, or None"
                },
            )

        logger.info(
            f"Updating default avatar image to {avatar_path if avatar_path else 'None'}"
        )
        return self.repository.update_default_avatar_image(avatar_path)

    def set_openrouter_api_key(self, api_key: str) -> ApplicationSettings:
        """Set the OpenRouter API key (encrypted storage).

        Args:
            api_key: The plaintext OpenRouter API key

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ValidationError: If the API key is invalid
            DatabaseError: If a database error occurs
        """
        if not api_key or not api_key.strip():
            raise ValidationError(
                "OpenRouter API key cannot be empty",
                details={"openrouter_api_key": "Must provide a valid API key"},
            )

        try:
            encrypted_key = encryption_service.encrypt_api_key(api_key.strip())
            logger.info("Setting OpenRouter API key (encrypted)")
            return self.repository.save_settings(
                openrouter_api_key_encrypted=encrypted_key
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to encrypt API key: {e}",
                details={"openrouter_api_key": "Encryption failed"},
            )

    def get_openrouter_api_key(self) -> Optional[str]:
        """Get the decrypted OpenRouter API key.

        Returns:
            The decrypted API key, or None if not set

        Raises:
            ValidationError: If decryption fails
            DatabaseError: If a database error occurs
        """
        settings = self.get_settings()
        if not settings.openrouter_api_key_encrypted:
            return None

        try:
            return encryption_service.decrypt_api_key(
                settings.openrouter_api_key_encrypted
            )
        except Exception as e:
            logger.error(f"Failed to decrypt OpenRouter API key: {e}")
            raise ValidationError(
                f"Failed to decrypt API key: {e}",
                details={"openrouter_api_key": "Decryption failed"},
            )

    def clear_openrouter_api_key(self) -> ApplicationSettings:
        """Clear the OpenRouter API key.

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Clearing OpenRouter API key")
        return self.repository.save_settings(openrouter_api_key_encrypted=None)

    def update_default_formatting_rules(
        self, formatting_rules: Optional[str] = None
    ) -> ApplicationSettings:
        """Update the default formatting rules.

        Args:
            formatting_rules: JSON string with default formatting rules, or None to clear

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ValidationError: If the formatting rules JSON is invalid
            DatabaseError: If a database error occurs
        """
        # Validate JSON if provided
        if formatting_rules is not None:
            import json

            try:
                json.loads(formatting_rules)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Invalid JSON in formatting rules: {e}",
                    details={"default_formatting_rules": "Must be valid JSON"},
                )

        logger.info(
            f"Updating default formatting rules to {'provided JSON' if formatting_rules else 'None'}"
        )
        return self.repository.save_settings(default_formatting_rules=formatting_rules)

    def get_default_formatting_rules(self) -> Optional[str]:
        """Get the default formatting rules.

        Returns:
            The default formatting rules JSON string, or None if not set

        Raises:
            DatabaseError: If a database error occurs
        """
        settings = self.get_settings()
        return settings.default_formatting_rules

    def update_settings(self, **kwargs) -> ApplicationSettings:
        """Update multiple application settings at once.

        Args:
            **kwargs: Settings attributes to update. Can include:
                - default_ai_model_id: New default AI model ID (optional)
                - default_system_prompt_id: New default system prompt ID (optional)
                - default_user_profile_id: New default user profile ID (optional)
                - default_avatar_image: New default avatar image path (optional)
                - default_formatting_rules: New default formatting rules JSON (optional)

        Returns:
            ApplicationSettings: The updated settings

        Raises:
            ResourceNotFoundError: If any referenced entity doesn't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Verify all entities exist if provided (and not None)
        if (
            "default_ai_model_id" in kwargs
            and kwargs["default_ai_model_id"] is not None
        ):
            self.ai_model_repository.get_by_id(kwargs["default_ai_model_id"])

        if (
            "default_system_prompt_id" in kwargs
            and kwargs["default_system_prompt_id"] is not None
        ):
            self.system_prompt_repository.get_by_id(kwargs["default_system_prompt_id"])

        if (
            "default_user_profile_id" in kwargs
            and kwargs["default_user_profile_id"] is not None
        ):
            self.user_profile_repository.get_by_id(kwargs["default_user_profile_id"])

        # Validate avatar path if provided
        if (
            "default_avatar_image" in kwargs
            and kwargs["default_avatar_image"] is not None
        ):
            if not kwargs["default_avatar_image"].strip():
                raise ValidationError(
                    "Avatar path cannot be empty string",
                    details={
                        "default_avatar_image": "Must provide a valid path or URL, or None"
                    },
                )

        # Validate formatting rules JSON if provided
        if (
            "default_formatting_rules" in kwargs
            and kwargs["default_formatting_rules"] is not None
        ):
            import json

            try:
                json.loads(kwargs["default_formatting_rules"])
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Invalid JSON in formatting rules: {e}",
                    details={"default_formatting_rules": "Must be valid JSON"},
                )

        logger.info("Updating multiple application settings")
        return self.repository.save_settings(**kwargs)

    def reset_settings(self) -> ApplicationSettings:
        """Reset all application settings to their defaults (None).

        Returns:
            ApplicationSettings: The reset settings

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Resetting all application settings to defaults")
        return self.repository.save_settings(
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
            default_formatting_rules=None,
        )
