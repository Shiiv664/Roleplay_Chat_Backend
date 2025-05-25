"""Service for ChatSession entity operations."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.models.chat_session import ChatSession
from app.repositories.ai_model_repository import AIModelRepository
from app.repositories.application_settings_repository import (
    ApplicationSettingsRepository,
)
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ChatSessionService:
    """Service for managing ChatSession entities.

    This service implements business logic and validation for ChatSession entities,
    using the ChatSessionRepository for data access along with other required repositories.
    """

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        character_repository: CharacterRepository,
        user_profile_repository: UserProfileRepository,
        ai_model_repository: AIModelRepository,
        system_prompt_repository: SystemPromptRepository,
        application_settings_repository: ApplicationSettingsRepository,
    ):
        """Initialize the service with repositories.

        Args:
            chat_session_repository: Repository for ChatSession data access
            character_repository: Repository for Character data access
            user_profile_repository: Repository for UserProfile data access
            ai_model_repository: Repository for AIModel data access
            system_prompt_repository: Repository for SystemPrompt data access
            application_settings_repository: Repository for ApplicationSettings data access
        """
        self.repository = chat_session_repository
        self.character_repository = character_repository
        self.user_profile_repository = user_profile_repository
        self.ai_model_repository = ai_model_repository
        self.system_prompt_repository = system_prompt_repository
        self.application_settings_repository = application_settings_repository

    def get_session(self, session_id: int) -> ChatSession:
        """Get a chat session by ID.

        Args:
            session_id: ID of the chat session to retrieve

        Returns:
            ChatSession: The requested chat session

        Raises:
            ResourceNotFoundError: If session with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting chat session with ID {session_id}")
        return self.repository.get_by_id(session_id)

    def get_session_with_relations(self, session_id: int) -> ChatSession:
        """Get a chat session by ID with all related entities preloaded.

        Args:
            session_id: ID of the chat session to retrieve

        Returns:
            ChatSession: The requested chat session with all relationships loaded

        Raises:
            ResourceNotFoundError: If session with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting chat session with ID {session_id} with all relations")
        return self.repository.get_by_id_with_relations(session_id)

    def get_sessions_by_character(self, character_id: int) -> List[ChatSession]:
        """Get all chat sessions for a specific character.

        Args:
            character_id: ID of the character to get sessions for

        Returns:
            List[ChatSession]: List of chat sessions for the character

        Raises:
            ResourceNotFoundError: If character does not exist
            DatabaseError: If a database error occurs
        """
        # Verify character exists
        self.character_repository.get_by_id(character_id)

        logger.info(f"Getting chat sessions for character with ID {character_id}")
        return self.repository.get_sessions_by_character_id(character_id)

    def get_sessions_by_user_profile(self, profile_id: int) -> List[ChatSession]:
        """Get all chat sessions for a specific user profile.

        Args:
            profile_id: ID of the user profile to get sessions for

        Returns:
            List[ChatSession]: List of chat sessions for the user profile

        Raises:
            ResourceNotFoundError: If user profile does not exist
            DatabaseError: If a database error occurs
        """
        # Verify user profile exists
        self.user_profile_repository.get_by_id(profile_id)

        logger.info(f"Getting chat sessions for user profile with ID {profile_id}")
        return self.repository.get_sessions_by_user_profile_id(profile_id)

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently updated chat sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List[ChatSession]: List of recent chat sessions

        Raises:
            ValidationError: If limit is invalid
            DatabaseError: If a database error occurs
        """
        if limit < 1:
            raise ValidationError("Limit must be a positive integer")

        logger.info(f"Getting {limit} most recent chat sessions")
        return self.repository.get_recent_sessions(limit=limit)

    def create_session(
        self,
        character_id: int,
        user_profile_id: int,
        ai_model_id: int,
        system_prompt_id: int,
        pre_prompt: Optional[str] = None,
        pre_prompt_enabled: bool = False,
        post_prompt: Optional[str] = None,
        post_prompt_enabled: bool = False,
    ) -> ChatSession:
        """Create a new chat session.

        Args:
            character_id: ID of the character to use in this session
            user_profile_id: ID of the user profile to use in this session
            ai_model_id: ID of the AI model to use in this session
            system_prompt_id: ID of the system prompt to use in this session
            pre_prompt: Optional text to add before each AI request (optional)
            pre_prompt_enabled: Whether the pre-prompt is enabled (default: False)
            post_prompt: Optional text to add after each AI request (optional)
            post_prompt_enabled: Whether the post-prompt is enabled (default: False)

        Returns:
            ChatSession: The created chat session

        Raises:
            ResourceNotFoundError: If any of the referenced entities don't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Validate that all referenced entities exist
        self._validate_session_entities(
            character_id, user_profile_id, ai_model_id, system_prompt_id
        )

        # Validate other inputs
        self._validate_session_data(
            pre_prompt, pre_prompt_enabled, post_prompt, post_prompt_enabled
        )

        # Create session
        session_data = {
            "character_id": character_id,
            "user_profile_id": user_profile_id,
            "ai_model_id": ai_model_id,
            "system_prompt_id": system_prompt_id,
            "pre_prompt": pre_prompt,
            "pre_prompt_enabled": pre_prompt_enabled,
            "post_prompt": post_prompt,
            "post_prompt_enabled": post_prompt_enabled,
            "start_time": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        logger.info(
            f"Creating chat session for character ID {character_id} "
            f"and user profile ID {user_profile_id}"
        )
        return self.repository.create(**session_data)

    def create_session_with_defaults(self, character_id: int) -> ChatSession:
        """Create a new chat session using application default settings.

        Args:
            character_id: ID of the character to use in this session

        Returns:
            ChatSession: The created chat session

        Raises:
            ResourceNotFoundError: If character doesn't exist or defaults are not configured
            ValidationError: If validation fails or required defaults are missing
            DatabaseError: If a database error occurs
        """
        # Validate that character exists
        self.character_repository.get_by_id(character_id)

        # Get application settings for defaults
        settings = self.application_settings_repository.get_settings()

        # Validate that all required defaults are configured
        missing_defaults = []
        if settings.default_user_profile_id is None:
            missing_defaults.append("default_user_profile_id")
        if settings.default_ai_model_id is None:
            missing_defaults.append("default_ai_model_id")
        if settings.default_system_prompt_id is None:
            missing_defaults.append("default_system_prompt_id")

        if missing_defaults:
            raise ValidationError(
                "Required default settings are not configured",
                details={
                    "missing_defaults": missing_defaults,
                    "message": "Please configure default settings before creating chat sessions",
                },
            )

        # Validate that the default entities still exist
        self._validate_session_entities(
            character_id,
            settings.default_user_profile_id,
            settings.default_ai_model_id,
            settings.default_system_prompt_id,
        )

        # Create session with defaults
        session_data = {
            "character_id": character_id,
            "user_profile_id": settings.default_user_profile_id,
            "ai_model_id": settings.default_ai_model_id,
            "system_prompt_id": settings.default_system_prompt_id,
            "pre_prompt": None,
            "pre_prompt_enabled": False,
            "post_prompt": None,
            "post_prompt_enabled": False,
            "start_time": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        logger.info(
            f"Creating chat session for character ID {character_id} "
            f"with default settings (user profile: {settings.default_user_profile_id}, "
            f"AI model: {settings.default_ai_model_id}, "
            f"system prompt: {settings.default_system_prompt_id})"
        )
        return self.repository.create(**session_data)

    def update_session(
        self,
        session_id: int,
        ai_model_id: Optional[int] = None,
        system_prompt_id: Optional[int] = None,
        pre_prompt: Optional[str] = None,
        pre_prompt_enabled: Optional[bool] = None,
        post_prompt: Optional[str] = None,
        post_prompt_enabled: Optional[bool] = None,
    ) -> ChatSession:
        """Update an existing chat session.

        Args:
            session_id: ID of the chat session to update
            ai_model_id: New AI model ID (optional)
            system_prompt_id: New system prompt ID (optional)
            pre_prompt: New pre-prompt text (optional)
            pre_prompt_enabled: New pre-prompt enabled flag (optional)
            post_prompt: New post-prompt text (optional)
            post_prompt_enabled: New post-prompt enabled flag (optional)

        Returns:
            ChatSession: The updated chat session

        Raises:
            ResourceNotFoundError: If session or any of the referenced entities don't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Get current session
        session = self.repository.get_by_id(session_id)

        # Prepare update data
        update_data = {}

        # Check and validate AI model if provided
        if ai_model_id is not None:
            self.ai_model_repository.get_by_id(ai_model_id)
            update_data["ai_model_id"] = ai_model_id

        # Check and validate system prompt if provided
        if system_prompt_id is not None:
            self.system_prompt_repository.get_by_id(system_prompt_id)
            update_data["system_prompt_id"] = system_prompt_id

        # Update pre-prompt if provided
        if pre_prompt is not None:
            update_data["pre_prompt"] = pre_prompt

        # Update pre-prompt enabled flag if provided
        if pre_prompt_enabled is not None:
            update_data["pre_prompt_enabled"] = pre_prompt_enabled

        # Update post-prompt if provided
        if post_prompt is not None:
            update_data["post_prompt"] = post_prompt

        # Update post-prompt enabled flag if provided
        if post_prompt_enabled is not None:
            update_data["post_prompt_enabled"] = post_prompt_enabled

        # If any changes, update the updated_at timestamp
        if update_data:
            update_data["updated_at"] = datetime.utcnow()

        # If no changes, just return the current session
        if not update_data:
            return session

        logger.info(f"Updating chat session with ID {session_id}")
        return self.repository.update(session_id, **update_data)

    def update_session_timestamp(self, session_id: int) -> None:
        """Update the timestamp of a chat session.

        This is useful when a new message is added to the session.

        Args:
            session_id: ID of the chat session to update

        Raises:
            ResourceNotFoundError: If session doesn't exist
            DatabaseError: If a database error occurs
        """
        logger.info(f"Updating timestamp for chat session with ID {session_id}")
        self.repository.update_session_timestamp(session_id)

    def delete_session(self, session_id: int) -> None:
        """Delete a chat session.

        Args:
            session_id: ID of the chat session to delete

        Raises:
            ResourceNotFoundError: If session doesn't exist
            DatabaseError: If a database error occurs
        """
        # Verify session exists
        self.repository.get_by_id(session_id)

        logger.info(f"Deleting chat session with ID {session_id}")
        self.repository.delete(session_id)

    def _validate_session_entities(
        self,
        character_id: int,
        user_profile_id: int,
        ai_model_id: int,
        system_prompt_id: int,
    ) -> None:
        """Validate that all entities referenced by a chat session exist.

        Args:
            character_id: ID of the character
            user_profile_id: ID of the user profile
            ai_model_id: ID of the AI model
            system_prompt_id: ID of the system prompt

        Raises:
            ResourceNotFoundError: If any of the entities don't exist
            DatabaseError: If a database error occurs
        """
        # No need to store these, just check they exist
        self.character_repository.get_by_id(character_id)
        self.user_profile_repository.get_by_id(user_profile_id)
        self.ai_model_repository.get_by_id(ai_model_id)
        self.system_prompt_repository.get_by_id(system_prompt_id)

    def _validate_session_data(
        self,
        pre_prompt: Optional[str],
        pre_prompt_enabled: bool,
        post_prompt: Optional[str],
        post_prompt_enabled: bool,
    ) -> None:
        """Validate chat session data.

        Args:
            pre_prompt: Pre-prompt text
            pre_prompt_enabled: Whether pre-prompt is enabled
            post_prompt: Post-prompt text
            post_prompt_enabled: Whether post-prompt is enabled

        Raises:
            ValidationError: If validation fails
        """
        errors: Dict[str, str] = {}

        # If pre-prompt is enabled, it must have a value
        if pre_prompt_enabled and not pre_prompt:
            errors["pre_prompt"] = (
                "Pre-prompt text is required when pre-prompt is enabled"
            )

        # If post-prompt is enabled, it must have a value
        if post_prompt_enabled and not post_prompt:
            errors["post_prompt"] = (
                "Post-prompt text is required when post-prompt is enabled"
            )

        if errors:
            raise ValidationError("Chat session validation failed", details=errors)
