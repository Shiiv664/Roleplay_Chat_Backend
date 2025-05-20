"""Tests for integration between service classes."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.services.ai_model_service import AIModelService
from app.services.application_settings_service import ApplicationSettingsService
from app.services.character_service import CharacterService
from app.services.chat_session_service import ChatSessionService
from app.services.message_service import MessageService
from app.services.system_prompt_service import SystemPromptService
from app.services.user_profile_service import UserProfileService


class TestServiceIntegration:
    """Test the integration between service classes."""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for all services."""
        return {
            "character_repository": MagicMock(),
            "user_profile_repository": MagicMock(),
            "ai_model_repository": MagicMock(),
            "system_prompt_repository": MagicMock(),
            "chat_session_repository": MagicMock(),
            "message_repository": MagicMock(),
            "application_settings_repository": MagicMock(),
        }

    @pytest.fixture
    def services(self, mock_repositories):
        """Create instances of all services with mock repositories."""
        # Character service
        character_service = CharacterService(mock_repositories["character_repository"])

        # User profile service
        user_profile_service = UserProfileService(
            mock_repositories["user_profile_repository"]
        )

        # AI model service
        ai_model_service = AIModelService(mock_repositories["ai_model_repository"])

        # System prompt service
        system_prompt_service = SystemPromptService(
            mock_repositories["system_prompt_repository"]
        )

        # Chat session service
        chat_session_service = ChatSessionService(
            mock_repositories["chat_session_repository"],
            mock_repositories["character_repository"],
            mock_repositories["user_profile_repository"],
            mock_repositories["ai_model_repository"],
            mock_repositories["system_prompt_repository"],
        )

        # Message service
        message_service = MessageService(
            mock_repositories["message_repository"],
            mock_repositories["chat_session_repository"],
        )

        # Application settings service
        application_settings_service = ApplicationSettingsService(
            mock_repositories["application_settings_repository"],
            mock_repositories["ai_model_repository"],
            mock_repositories["system_prompt_repository"],
            mock_repositories["user_profile_repository"],
        )

        return {
            "character_service": character_service,
            "user_profile_service": user_profile_service,
            "ai_model_service": ai_model_service,
            "system_prompt_service": system_prompt_service,
            "chat_session_service": chat_session_service,
            "message_service": message_service,
            "application_settings_service": application_settings_service,
        }

    @pytest.fixture
    def sample_chat_session(self):
        """Create a sample chat session for testing."""
        return ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=1,
            system_prompt_id=1,
            start_time=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def test_create_chat_session_and_message(
        self, services, mock_repositories, sample_chat_session
    ):
        """Test creating a chat session and adding messages to it."""
        # Setup
        mock_repositories["character_repository"].get_by_id.return_value = MagicMock()
        mock_repositories["user_profile_repository"].get_by_id.return_value = (
            MagicMock()
        )
        mock_repositories["ai_model_repository"].get_by_id.return_value = MagicMock()
        mock_repositories["system_prompt_repository"].get_by_id.return_value = (
            MagicMock()
        )
        mock_repositories["chat_session_repository"].create.return_value = (
            sample_chat_session
        )

        user_message = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Hello AI",
        )
        assistant_message = Message(
            id=2,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="Hello human",
        )
        mock_repositories["message_repository"].create.side_effect = [
            user_message,
            assistant_message,
        ]

        # Execute
        # 1. Create a chat session
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = sample_chat_session.start_time
            services["chat_session_service"].create_session(
                character_id=1,
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
            )

        # 2. Create a user message
        services["message_service"].create_user_message(
            session_id=1,
            content="Hello AI",
        )

        # 3. Create an assistant message
        services["message_service"].create_assistant_message(
            session_id=1,
            content="Hello human",
        )

        # Verify
        # Chat session created correctly
        mock_repositories["chat_session_repository"].create.assert_called_once()

        # Messages created correctly
        assert mock_repositories["message_repository"].create.call_count == 2
        call_args_list = mock_repositories["message_repository"].create.call_args_list
        assert call_args_list[0][1]["chat_session_id"] == 1
        assert call_args_list[0][1]["role"] == MessageRole.USER
        assert call_args_list[0][1]["content"] == "Hello AI"
        assert call_args_list[1][1]["chat_session_id"] == 1
        assert call_args_list[1][1]["role"] == MessageRole.ASSISTANT
        assert call_args_list[1][1]["content"] == "Hello human"

        # Chat session timestamp updated for each message
        assert (
            mock_repositories[
                "chat_session_repository"
            ].update_session_timestamp.call_count
            == 2
        )
        mock_repositories[
            "chat_session_repository"
        ].update_session_timestamp.assert_any_call(1)

    def test_defaults_from_application_settings(
        self, services, mock_repositories, sample_chat_session
    ):
        """Test creating a chat session using defaults from application settings."""
        # Setup - mock application settings with defaults
        mock_application_settings = MagicMock()
        mock_application_settings.default_ai_model_id = 2
        mock_application_settings.default_system_prompt_id = 3
        mock_application_settings.default_user_profile_id = 4
        mock_repositories[
            "application_settings_repository"
        ].get_settings.return_value = mock_application_settings

        # Mock other repositories
        mock_repositories["character_repository"].get_by_id.return_value = MagicMock()
        mock_repositories["user_profile_repository"].get_by_id.return_value = (
            MagicMock()
        )
        mock_repositories["ai_model_repository"].get_by_id.return_value = MagicMock()
        mock_repositories["system_prompt_repository"].get_by_id.return_value = (
            MagicMock()
        )

        # Modified chat session with default values
        default_session = ChatSession(
            id=1,
            character_id=1,  # Character always needs to be specified
            user_profile_id=4,  # From defaults
            ai_model_id=2,  # From defaults
            system_prompt_id=3,  # From defaults
            start_time=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repositories["chat_session_repository"].create.return_value = (
            default_session
        )

        # Execute
        # 1. Get default settings
        settings = services["application_settings_service"].get_settings()

        # 2. Create chat session using defaults
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = default_session.start_time
            services["chat_session_service"].create_session(
                character_id=1,  # Character still needs to be specified
                user_profile_id=settings.default_user_profile_id,
                ai_model_id=settings.default_ai_model_id,
                system_prompt_id=settings.default_system_prompt_id,
            )

        # Verify
        mock_repositories[
            "application_settings_repository"
        ].get_settings.assert_called_once()
        mock_repositories["character_repository"].get_by_id.assert_called_once_with(1)
        mock_repositories["user_profile_repository"].get_by_id.assert_called_once_with(
            4
        )
        mock_repositories["ai_model_repository"].get_by_id.assert_called_once_with(2)
        mock_repositories["system_prompt_repository"].get_by_id.assert_called_once_with(
            3
        )
        mock_repositories["chat_session_repository"].create.assert_called_once()

        # Verify the chat session was created with the correct default values
        create_kwargs = mock_repositories["chat_session_repository"].create.call_args[1]
        assert create_kwargs["character_id"] == 1
        assert create_kwargs["user_profile_id"] == 4  # Default from settings
        assert create_kwargs["ai_model_id"] == 2  # Default from settings
        assert create_kwargs["system_prompt_id"] == 3  # Default from settings

    def test_update_chat_session_and_add_message(
        self, services, mock_repositories, sample_chat_session
    ):
        """Test updating a chat session and adding a message."""
        # Setup
        mock_repositories["chat_session_repository"].get_by_id.return_value = (
            sample_chat_session
        )
        mock_repositories["ai_model_repository"].get_by_id.return_value = MagicMock()

        updated_session = ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=2,  # Updated
            system_prompt_id=1,
            start_time=sample_chat_session.start_time,
            updated_at=datetime.utcnow(),  # Updated
        )
        mock_repositories["chat_session_repository"].update.return_value = (
            updated_session
        )

        message = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="This is a new message",
        )
        mock_repositories["message_repository"].create.return_value = message

        # Execute
        # 1. Update the chat session
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = updated_session.updated_at
            services["chat_session_service"].update_session(
                session_id=1,
                ai_model_id=2,  # Change AI model
            )

        # 2. Add a message to the updated session
        services["message_service"].create_user_message(
            session_id=1,
            content="This is a new message",
        )

        # Verify
        # get_by_id is called twice: once by update_session and once by create_user_message
        assert mock_repositories["chat_session_repository"].get_by_id.call_count == 2
        mock_repositories["chat_session_repository"].get_by_id.assert_called_with(1)
        mock_repositories["ai_model_repository"].get_by_id.assert_called_once_with(2)
        mock_repositories["chat_session_repository"].update.assert_called_once()

        # Verify the chat session was updated correctly
        update_kwargs = mock_repositories["chat_session_repository"].update.call_args[1]
        assert update_kwargs["ai_model_id"] == 2
        assert "updated_at" in update_kwargs

        # Verify the message was created correctly
        mock_repositories["message_repository"].create.assert_called_once_with(
            chat_session_id=1,
            role=MessageRole.USER,
            content="This is a new message",
        )

        # Verify the chat session timestamp was updated when the message was added
        mock_repositories[
            "chat_session_repository"
        ].update_session_timestamp.assert_called_once_with(1)

    def test_full_chat_flow(self, services, mock_repositories):
        """Test a full chat flow from creating entities to sending messages."""
        # Setup - mock all repository responses for a full chat flow

        # Get character, user, AI model, and system prompt
        mock_repositories["character_repository"].get_by_id.return_value = MagicMock(
            id=1
        )
        mock_repositories["user_profile_repository"].get_by_id.return_value = MagicMock(
            id=1
        )
        mock_repositories["ai_model_repository"].get_by_id.return_value = MagicMock(
            id=1
        )
        mock_repositories["system_prompt_repository"].get_by_id.return_value = (
            MagicMock(id=1)
        )

        # Create chat session
        chat_session = ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=1,
            system_prompt_id=1,
            start_time=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repositories["chat_session_repository"].create.return_value = chat_session
        mock_repositories["chat_session_repository"].get_by_id.return_value = (
            chat_session
        )

        # Messages
        user_message1 = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Hello, how are you?",
        )
        assistant_message1 = Message(
            id=2,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="I'm doing well, thank you for asking!",
        )
        user_message2 = Message(
            id=3,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Tell me a story",
        )
        assistant_message2 = Message(
            id=4,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="Once upon a time...",
        )

        # Mock message creation
        mock_repositories["message_repository"].create.side_effect = [
            user_message1,
            assistant_message1,
            user_message2,
            assistant_message2,
        ]

        # Mock getting messages
        mock_repositories["message_repository"].get_by_chat_session_id.return_value = [
            user_message1,
            assistant_message1,
            user_message2,
            assistant_message2,
        ]

        # Execute the full flow

        # 1. Create the chat session
        with patch("app.services.chat_session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = chat_session.start_time
            services["chat_session_service"].create_session(
                character_id=1,
                user_profile_id=1,
                ai_model_id=1,
                system_prompt_id=1,
            )

        # 2. First user message
        services["message_service"].create_user_message(
            session_id=1,
            content="Hello, how are you?",
        )

        # 3. First assistant response
        services["message_service"].create_assistant_message(
            session_id=1,
            content="I'm doing well, thank you for asking!",
        )

        # 4. Second user message
        services["message_service"].create_user_message(
            session_id=1,
            content="Tell me a story",
        )

        # 5. Second assistant response
        services["message_service"].create_assistant_message(
            session_id=1,
            content="Once upon a time...",
        )

        # 6. Retrieve all messages
        messages = services["message_service"].get_messages_by_chat_session(1)

        # Verify
        # Chat session created correctly
        mock_repositories["chat_session_repository"].create.assert_called_once()

        # Messages created correctly
        assert mock_repositories["message_repository"].create.call_count == 4

        # Chat session timestamp updated for each message
        assert (
            mock_repositories[
                "chat_session_repository"
            ].update_session_timestamp.call_count
            == 4
        )

        # Messages retrieved correctly
        mock_repositories[
            "message_repository"
        ].get_by_chat_session_id.assert_called_once_with(1, None, None)
        assert len(messages) == 4
        assert messages[0].content == "Hello, how are you?"
        assert messages[1].content == "I'm doing well, thank you for asking!"
        assert messages[2].content == "Tell me a story"
        assert messages[3].content == "Once upon a time..."
