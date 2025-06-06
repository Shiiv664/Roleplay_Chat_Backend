"""Tests for the ChatSessionService class."""

from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from app.models.chat_session import ChatSession
from app.services.chat_session_service import ChatSessionService
from app.utils.exceptions import ResourceNotFoundError, ValidationError


class TestChatSessionService:
    """Test the ChatSessionService functionality."""

    @pytest.fixture
    def mock_chat_session_repository(self):
        """Create a mock chat session repository."""
        return MagicMock()

    @pytest.fixture
    def mock_character_repository(self):
        """Create a mock character repository."""
        return MagicMock()

    @pytest.fixture
    def mock_user_profile_repository(self):
        """Create a mock user profile repository."""
        return MagicMock()

    @pytest.fixture
    def mock_ai_model_repository(self):
        """Create a mock AI model repository."""
        return MagicMock()

    @pytest.fixture
    def mock_system_prompt_repository(self):
        """Create a mock system prompt repository."""
        return MagicMock()

    @pytest.fixture
    def mock_application_settings_repository(self):
        """Create a mock application settings repository."""
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_chat_session_repository,
        mock_character_repository,
        mock_user_profile_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        mock_application_settings_repository,
    ):
        """Create a ChatSessionService with mock repositories."""
        return ChatSessionService(
            mock_chat_session_repository,
            mock_character_repository,
            mock_user_profile_repository,
            mock_ai_model_repository,
            mock_system_prompt_repository,
            mock_application_settings_repository,
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample chat session for testing."""
        return ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=1,
            system_prompt_id=1,
            start_time=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            pre_prompt="Optional pre-prompt",
            pre_prompt_enabled=True,
            post_prompt="Optional post-prompt",
            post_prompt_enabled=False,
        )

    def test_get_session(self, service, mock_chat_session_repository, sample_session):
        """Test getting a chat session by ID."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session

        # Execute
        result = service.get_session(1)

        # Verify
        assert result == sample_session
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)

    def test_get_session_with_relations(
        self, service, mock_chat_session_repository, sample_session
    ):
        """Test getting a chat session with relations."""
        # Setup
        mock_chat_session_repository.get_by_id_with_relations.return_value = (
            sample_session
        )

        # Execute
        result = service.get_session_with_relations(1)

        # Verify
        assert result == sample_session
        mock_chat_session_repository.get_by_id_with_relations.assert_called_once_with(1)

    def test_get_sessions_by_character(
        self,
        service,
        mock_chat_session_repository,
        mock_character_repository,
        sample_session,
    ):
        """Test getting all sessions for a character."""
        # Setup
        mock_character_repository.get_by_id.return_value = (
            MagicMock()
        )  # Character exists
        mock_chat_session_repository.get_sessions_by_character_id.return_value = [
            sample_session
        ]

        # Execute
        result = service.get_sessions_by_character(1)

        # Verify
        assert result == [sample_session]
        mock_character_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.get_sessions_by_character_id.assert_called_once_with(
            1
        )

    def test_get_sessions_by_character_not_found(
        self, service, mock_chat_session_repository, mock_character_repository
    ):
        """Test getting sessions for non-existent character."""
        # Setup
        mock_character_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.get_sessions_by_character(999)

        # Verify repository method was not called
        mock_chat_session_repository.get_sessions_by_character_id.assert_not_called()

    def test_get_sessions_by_user_profile(
        self,
        service,
        mock_chat_session_repository,
        mock_user_profile_repository,
        sample_session,
    ):
        """Test getting all sessions for a user profile."""
        # Setup
        mock_user_profile_repository.get_by_id.return_value = (
            MagicMock()
        )  # Profile exists
        mock_chat_session_repository.get_sessions_by_user_profile_id.return_value = [
            sample_session
        ]

        # Execute
        result = service.get_sessions_by_user_profile(1)

        # Verify
        assert result == [sample_session]
        mock_user_profile_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.get_sessions_by_user_profile_id.assert_called_once_with(
            1
        )

    def test_get_sessions_by_user_profile_not_found(
        self, service, mock_chat_session_repository, mock_user_profile_repository
    ):
        """Test getting sessions for non-existent user profile."""
        # Setup
        mock_user_profile_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.get_sessions_by_user_profile(999)

        # Verify repository method was not called
        mock_chat_session_repository.get_sessions_by_user_profile_id.assert_not_called()

    def test_get_recent_sessions(
        self, service, mock_chat_session_repository, sample_session
    ):
        """Test getting recent sessions."""
        # Setup
        mock_chat_session_repository.get_recent_sessions.return_value = [sample_session]

        # Execute
        result = service.get_recent_sessions(5)

        # Verify
        assert result == [sample_session]
        mock_chat_session_repository.get_recent_sessions.assert_called_once_with(
            limit=5
        )

    def test_get_recent_sessions_invalid_limit(
        self, service, mock_chat_session_repository
    ):
        """Test getting recent sessions with invalid limit."""
        # Execute and verify
        with pytest.raises(ValidationError):
            service.get_recent_sessions(0)

        with pytest.raises(ValidationError):
            service.get_recent_sessions(-1)

        # Verify repository method was not called
        mock_chat_session_repository.get_recent_sessions.assert_not_called()

    def test_create_session(
        self,
        service,
        mock_chat_session_repository,
        mock_character_repository,
        mock_user_profile_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        sample_session,
    ):
        """Test creating a new chat session."""
        # Setup - all entities exist
        mock_character_repository.get_by_id.return_value = MagicMock()
        mock_user_profile_repository.get_by_id.return_value = MagicMock()
        mock_ai_model_repository.get_by_id.return_value = MagicMock()
        mock_system_prompt_repository.get_by_id.return_value = MagicMock()
        mock_chat_session_repository.create.return_value = sample_session

        # Execute
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = sample_session.start_time
            result = service.create_session(
                character_id=1,
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
                pre_prompt="Optional pre-prompt",
                pre_prompt_enabled=True,
                post_prompt="Optional post-prompt",
                post_prompt_enabled=False,
            )

        # Verify
        assert result == sample_session
        mock_character_repository.get_by_id.assert_called_once_with(1)
        mock_user_profile_repository.get_by_id.assert_called_once_with(1)
        mock_ai_model_repository.get_by_id.assert_called_once_with(1)
        mock_system_prompt_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.create.assert_called_once()
        # Check the kwargs passed to create
        create_kwargs = mock_chat_session_repository.create.call_args[1]
        assert create_kwargs["character_id"] == 1
        assert create_kwargs["user_profile_id"] == 1
        assert create_kwargs["ai_model_id"] == 1
        assert create_kwargs["system_prompt_id"] == 1
        assert create_kwargs["pre_prompt"] == "Optional pre-prompt"
        assert create_kwargs["pre_prompt_enabled"] is True
        assert create_kwargs["post_prompt"] == "Optional post-prompt"
        assert create_kwargs["post_prompt_enabled"] is False

    def test_create_session_entity_not_found(
        self,
        service,
        mock_chat_session_repository,
        mock_character_repository,
    ):
        """Test creating a chat session with non-existent character."""
        # Setup
        mock_character_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.create_session(
                character_id=999,  # Non-existent
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
            )

        # Verify repository method was not called
        mock_chat_session_repository.create.assert_not_called()

    def test_create_session_validation_error(
        self,
        service,
        mock_chat_session_repository,
        mock_character_repository,
        mock_user_profile_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
    ):
        """Test creating a chat session with invalid data."""
        # Setup - all entities exist
        mock_character_repository.get_by_id.return_value = MagicMock()
        mock_user_profile_repository.get_by_id.return_value = MagicMock()
        mock_ai_model_repository.get_by_id.return_value = MagicMock()
        mock_system_prompt_repository.get_by_id.return_value = MagicMock()

        # Execute and verify - pre_prompt_enabled but no pre_prompt
        with pytest.raises(ValidationError) as excinfo:
            service.create_session(
                character_id=1,
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
                pre_prompt=None,
                pre_prompt_enabled=True,  # Enabled but no text
            )

        assert "pre_prompt" in excinfo.value.details
        mock_chat_session_repository.create.assert_not_called()

        # Execute and verify - post_prompt_enabled but no post_prompt
        with pytest.raises(ValidationError) as excinfo:
            service.create_session(
                character_id=1,
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
                post_prompt=None,
                post_prompt_enabled=True,  # Enabled but no text
            )

        assert "post_prompt" in excinfo.value.details
        mock_chat_session_repository.create.assert_not_called()

    def test_create_session_with_defaults(
        self,
        service,
        mock_chat_session_repository,
        mock_character_repository,
        mock_application_settings_repository,
        sample_session,
    ):
        """Test creating a new chat session with default settings."""
        # Setup - character exists and defaults are configured
        mock_character_repository.get_by_id.return_value = MagicMock()

        # Mock application settings with defaults
        mock_settings = MagicMock()
        mock_settings.default_user_profile_id = 1
        mock_settings.default_ai_model_id = 2
        mock_settings.default_system_prompt_id = 3
        mock_application_settings_repository.get_settings.return_value = mock_settings

        # Mock validation of default entities
        service.user_profile_repository.get_by_id.return_value = MagicMock()
        service.ai_model_repository.get_by_id.return_value = MagicMock()
        service.system_prompt_repository.get_by_id.return_value = MagicMock()

        mock_chat_session_repository.create.return_value = sample_session

        # Execute
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = sample_session.start_time
            result = service.create_session_with_defaults(character_id=5)

        # Verify
        assert result == sample_session
        # Character repository is called twice: once for initial validation, once in _validate_session_entities
        assert mock_character_repository.get_by_id.call_count == 2
        mock_character_repository.get_by_id.assert_has_calls([call(5), call(5)])
        mock_application_settings_repository.get_settings.assert_called_once()

        # Verify default entities were validated
        service.user_profile_repository.get_by_id.assert_called_once_with(1)
        service.ai_model_repository.get_by_id.assert_called_once_with(2)
        service.system_prompt_repository.get_by_id.assert_called_once_with(3)

        # Verify session was created with defaults
        mock_chat_session_repository.create.assert_called_once()
        call_args = mock_chat_session_repository.create.call_args[1]
        assert call_args["character_id"] == 5
        assert call_args["user_profile_id"] == 1
        assert call_args["ai_model_id"] == 2
        assert call_args["system_prompt_id"] == 3
        assert call_args["pre_prompt"] is None
        assert call_args["pre_prompt_enabled"] is False
        assert call_args["post_prompt"] is None
        assert call_args["post_prompt_enabled"] is False

    def test_create_session_with_defaults_missing_defaults(
        self,
        service,
        mock_character_repository,
        mock_application_settings_repository,
    ):
        """Test creating session with defaults when required defaults are missing."""
        # Setup - character exists but defaults are not configured
        mock_character_repository.get_by_id.return_value = MagicMock()

        # Mock application settings with missing defaults
        mock_settings = MagicMock()
        mock_settings.default_user_profile_id = None
        mock_settings.default_ai_model_id = 2
        mock_settings.default_system_prompt_id = 3
        mock_application_settings_repository.get_settings.return_value = mock_settings

        # Execute and verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_session_with_defaults(character_id=5)

        assert "Required default settings are not configured" in str(excinfo.value)
        assert "default_user_profile_id" in excinfo.value.details["missing_defaults"]

    def test_create_session_with_defaults_character_not_found(
        self,
        service,
        mock_character_repository,
    ):
        """Test creating session with defaults when character doesn't exist."""
        # Setup - character doesn't exist
        mock_character_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Character with ID 999 not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.create_session_with_defaults(character_id=999)

        mock_character_repository.get_by_id.assert_called_once_with(999)

    def test_update_session(
        self,
        service,
        mock_chat_session_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        sample_session,
    ):
        """Test updating a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session
        mock_ai_model_repository.get_by_id.return_value = MagicMock()
        mock_system_prompt_repository.get_by_id.return_value = MagicMock()

        updated_session = ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=2,  # Changed
            system_prompt_id=2,  # Changed
            start_time=sample_session.start_time,
            updated_at=datetime.utcnow(),  # Updated
            pre_prompt="New pre-prompt",  # Changed
            pre_prompt_enabled=False,  # Changed
            post_prompt="New post-prompt",  # Changed
            post_prompt_enabled=True,  # Changed
        )
        mock_chat_session_repository.update.return_value = updated_session

        # Execute
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = updated_session.updated_at
            result = service.update_session(
                session_id=1,
                ai_model_id=2,
                system_prompt_id=2,
                pre_prompt="New pre-prompt",
                pre_prompt_enabled=False,
                post_prompt="New post-prompt",
                post_prompt_enabled=True,
            )

        # Verify
        assert result == updated_session
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_ai_model_repository.get_by_id.assert_called_once_with(2)
        mock_system_prompt_repository.get_by_id.assert_called_once_with(2)
        mock_chat_session_repository.update.assert_called_once()
        # Check the kwargs passed to update
        update_kwargs = mock_chat_session_repository.update.call_args[1]
        assert update_kwargs["ai_model_id"] == 2
        assert update_kwargs["system_prompt_id"] == 2
        assert update_kwargs["pre_prompt"] == "New pre-prompt"
        assert update_kwargs["pre_prompt_enabled"] is False
        assert update_kwargs["post_prompt"] == "New post-prompt"
        assert update_kwargs["post_prompt_enabled"] is True
        assert "updated_at" in update_kwargs

    def test_update_session_partial(
        self,
        service,
        mock_chat_session_repository,
        sample_session,
    ):
        """Test partial update of a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session

        updated_session = ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=1,
            system_prompt_id=1,
            start_time=sample_session.start_time,
            updated_at=datetime.utcnow(),  # Updated
            pre_prompt="New pre-prompt",  # Only this changed
            pre_prompt_enabled=True,
            post_prompt="Optional post-prompt",
            post_prompt_enabled=False,
        )
        mock_chat_session_repository.update.return_value = updated_session

        # Execute - only update pre_prompt
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = updated_session.updated_at
            result = service.update_session(
                session_id=1,
                pre_prompt="New pre-prompt",
            )

        # Verify
        assert result == updated_session
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.update.assert_called_once()
        # Check the kwargs passed to update
        update_kwargs = mock_chat_session_repository.update.call_args[1]
        assert len(update_kwargs) == 2  # Only pre_prompt and updated_at
        assert update_kwargs["pre_prompt"] == "New pre-prompt"
        assert "updated_at" in update_kwargs

    def test_update_session_no_changes(
        self,
        service,
        mock_chat_session_repository,
        sample_session,
    ):
        """Test update of a chat session with no changes."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session

        # Execute - no changes
        result = service.update_session(session_id=1)

        # Verify
        assert result == sample_session
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.update.assert_not_called()

    def test_update_session_entity_not_found(
        self,
        service,
        mock_chat_session_repository,
        mock_ai_model_repository,
        sample_session,
    ):
        """Test updating a chat session with non-existent AI model."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session
        mock_ai_model_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_session(
                session_id=1,
                ai_model_id=999,  # Non-existent
            )

        # Verify repository method was not called
        mock_chat_session_repository.update.assert_not_called()

    def test_update_session_timestamp(
        self,
        service,
        mock_chat_session_repository,
    ):
        """Test updating a chat session timestamp."""
        # Execute
        service.update_session_timestamp(1)

        # Verify
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_delete_session(
        self,
        service,
        mock_chat_session_repository,
        sample_session,
    ):
        """Test deleting a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = sample_session

        # Execute
        service.delete_session(1)

        # Verify
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_chat_session_repository.delete.assert_called_once_with(1)

    def test_delete_session_not_found(
        self,
        service,
        mock_chat_session_repository,
    ):
        """Test deleting a non-existent chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.delete_session(999)

        # Verify repository method was not called
        mock_chat_session_repository.delete.assert_not_called()
