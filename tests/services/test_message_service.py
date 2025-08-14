"""Tests for the MessageService class."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.ai_model import AIModel
from app.models.character import Character
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile
from app.services.message_service import MessageService
from app.utils.exceptions import BusinessRuleError, ResourceNotFoundError, ValidationError


class TestMessageService:
    """Test the MessageService functionality."""

    @pytest.fixture
    def mock_message_repository(self):
        """Create a mock message repository."""
        return MagicMock()

    @pytest.fixture
    def mock_chat_session_repository(self):
        """Create a mock chat session repository."""
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_message_repository,
        mock_chat_session_repository,
    ):
        """Create a MessageService with mock repositories."""
        return MessageService(
            mock_message_repository,
            mock_chat_session_repository,
        )

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing."""
        return Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="This is a test message",
        )

    def test_get_message(self, service, mock_message_repository, sample_message):
        """Test getting a message by ID."""
        # Setup
        mock_message_repository.get_by_id.return_value = sample_message

        # Execute
        result = service.get_message(1)

        # Verify
        assert result == sample_message
        mock_message_repository.get_by_id.assert_called_once_with(1)

    def test_get_messages_by_chat_session(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test getting messages for a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.get_by_chat_session_id.return_value = [sample_message]

        # Execute
        result = service.get_messages_by_chat_session(1)

        # Verify
        assert result == [sample_message]
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.get_by_chat_session_id.assert_called_once_with(
            1, None, None
        )

    def test_get_messages_by_chat_session_with_pagination(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test getting messages for a chat session with pagination."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.get_by_chat_session_id.return_value = [sample_message]

        # Execute
        result = service.get_messages_by_chat_session(1, limit=10, offset=20)

        # Verify
        assert result == [sample_message]
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.get_by_chat_session_id.assert_called_once_with(
            1, 10, 20
        )

    def test_get_messages_by_chat_session_invalid_pagination(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test getting messages with invalid pagination parameters."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Execute and verify - invalid limit
        with pytest.raises(ValidationError):
            service.get_messages_by_chat_session(1, limit=0)

        with pytest.raises(ValidationError):
            service.get_messages_by_chat_session(1, limit=-1)

        # Execute and verify - invalid offset
        with pytest.raises(ValidationError):
            service.get_messages_by_chat_session(1, offset=-1)

        # Verify repository method was not called
        mock_message_repository.get_by_chat_session_id.assert_not_called()

    def test_get_messages_by_chat_session_not_found(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test getting messages for non-existent chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.get_messages_by_chat_session(999)

        # Verify repository method was not called
        mock_message_repository.get_by_chat_session_id.assert_not_called()

    def test_get_paged_messages(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test getting paginated messages for a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        pagination = {
            "total_count": 100,
            "total_pages": 10,
            "current_page": 1,
            "page_size": 10,
            "has_next": True,
            "has_previous": False,
        }
        mock_message_repository.get_paged_messages.return_value = (
            [sample_message],
            pagination,
        )

        # Execute
        messages, paging = service.get_paged_messages(1, page=1, page_size=10)

        # Verify
        assert messages == [sample_message]
        assert paging == pagination
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.get_paged_messages.assert_called_once_with(1, 1, 10)

    def test_get_paged_messages_invalid_pagination(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test getting paged messages with invalid pagination parameters."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Execute and verify - invalid page
        with pytest.raises(ValidationError):
            service.get_paged_messages(1, page=0)

        with pytest.raises(ValidationError):
            service.get_paged_messages(1, page=-1)

        # Execute and verify - invalid page size
        with pytest.raises(ValidationError):
            service.get_paged_messages(1, page_size=0)

        with pytest.raises(ValidationError):
            service.get_paged_messages(1, page_size=-1)

        # Verify repository method was not called
        mock_message_repository.get_paged_messages.assert_not_called()

    def test_get_latest_messages(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test getting latest messages for a chat session."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.get_latest_messages.return_value = [sample_message]

        # Execute
        result = service.get_latest_messages(1, count=5)

        # Verify
        assert result == [sample_message]
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.get_latest_messages.assert_called_once_with(1, 5)

    def test_get_latest_messages_invalid_count(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test getting latest messages with invalid count."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Execute and verify
        with pytest.raises(ValidationError):
            service.get_latest_messages(1, count=0)

        with pytest.raises(ValidationError):
            service.get_latest_messages(1, count=-1)

        # Verify repository method was not called
        mock_message_repository.get_latest_messages.assert_not_called()

    def test_create_message(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test creating a new message."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.create.return_value = sample_message

        # Execute
        result = service.create_message(
            session_id=1,
            role=MessageRole.USER,
            content="This is a test message",
        )

        # Verify
        assert result == sample_message
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.create.assert_called_once_with(
            chat_session_id=1,
            role=MessageRole.USER,
            content="This is a test message",
        )
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_create_message_string_role(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test creating a new message with string role."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.create.return_value = sample_message

        # Execute
        result = service.create_message(
            session_id=1,
            role="user",  # String instead of enum
            content="This is a test message",
        )

        # Verify
        assert result == sample_message
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        # Verify role was converted to enum
        mock_message_repository.create.assert_called_once()
        create_kwargs = mock_message_repository.create.call_args[1]
        assert create_kwargs["role"] == MessageRole.USER
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_create_message_invalid_role(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test creating a message with invalid role."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Execute and verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_message(
                session_id=1,
                role="invalid_role",  # Invalid role
                content="This is a test message",
            )

        assert "role" in excinfo.value.details
        mock_message_repository.create.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()

    def test_create_message_empty_content(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test creating a message with empty content."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Execute and verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_message(
                session_id=1,
                role=MessageRole.USER,
                content="",  # Empty content
            )

        assert "content" in excinfo.value.details
        mock_message_repository.create.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()

    def test_create_user_message(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test creating a user message."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        mock_message_repository.create.return_value = sample_message

        # Execute
        result = service.create_user_message(
            session_id=1,
            content="This is a test message",
        )

        # Verify
        assert result == sample_message
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.create.assert_called_once_with(
            chat_session_id=1,
            role=MessageRole.USER,
            content="This is a test message",
        )
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_create_assistant_message(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test creating an assistant message."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        assistant_message = Message(
            id=2,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="This is an assistant response",
        )
        mock_message_repository.create.return_value = assistant_message

        # Execute
        result = service.create_assistant_message(
            session_id=1,
            content="This is an assistant response",
        )

        # Verify
        assert result == assistant_message
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.create.assert_called_once_with(
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="This is an assistant response",
        )
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_create_bulk_messages(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test creating multiple messages in bulk."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists
        message2 = Message(
            id=2,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="This is a response",
        )
        mock_message_repository.create_bulk.return_value = [sample_message, message2]

        messages_data = [
            {
                "chat_session_id": 1,
                "role": MessageRole.USER,
                "content": "This is a test message",
            },
            {
                "chat_session_id": 1,
                "role": MessageRole.ASSISTANT,
                "content": "This is a response",
            },
        ]

        # Execute
        result = service.create_bulk_messages(messages_data)

        # Verify
        assert result == [sample_message, message2]
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.create_bulk.assert_called_once_with(messages_data)
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_create_bulk_messages_multiple_sessions(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test creating messages for multiple chat sessions in bulk."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat sessions exist
        message1 = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Message for session 1",
        )
        message2 = Message(
            id=2,
            chat_session_id=2,
            role=MessageRole.USER,
            content="Message for session 2",
        )
        mock_message_repository.create_bulk.return_value = [message1, message2]

        messages_data = [
            {
                "chat_session_id": 1,
                "role": MessageRole.USER,
                "content": "Message for session 1",
            },
            {
                "chat_session_id": 2,
                "role": MessageRole.USER,
                "content": "Message for session 2",
            },
        ]

        # Execute
        result = service.create_bulk_messages(messages_data)

        # Verify
        assert result == [message1, message2]
        # Should have called get_by_id for both session IDs
        assert mock_chat_session_repository.get_by_id.call_count == 2
        mock_message_repository.create_bulk.assert_called_once_with(messages_data)
        # Should have updated timestamp for both sessions
        assert mock_chat_session_repository.update_session_timestamp.call_count == 2
        mock_chat_session_repository.update_session_timestamp.assert_any_call(1)
        mock_chat_session_repository.update_session_timestamp.assert_any_call(2)

    def test_create_bulk_messages_string_role(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test creating messages with string roles in bulk."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        messages_data = [
            {
                "chat_session_id": 1,
                "role": "user",  # String instead of enum
                "content": "This is a test message",
            },
            {
                "chat_session_id": 1,
                "role": "assistant",  # String instead of enum
                "content": "This is a response",
            },
        ]

        # Execute
        service.create_bulk_messages(messages_data)

        # Verify
        mock_chat_session_repository.get_by_id.assert_called_once_with(1)
        # Verify roles were converted to enums
        assert messages_data[0]["role"] == MessageRole.USER
        assert messages_data[1]["role"] == MessageRole.ASSISTANT
        mock_message_repository.create_bulk.assert_called_once()

    def test_create_bulk_messages_validation_errors(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test bulk message creation with various validation errors."""
        # Setup
        mock_chat_session_repository.get_by_id.return_value = (
            MagicMock()
        )  # Chat session exists

        # Test with empty list
        with pytest.raises(ValidationError):
            service.create_bulk_messages([])

        # Test with missing required field
        with pytest.raises(ValidationError) as excinfo:
            service.create_bulk_messages(
                [
                    {
                        "chat_session_id": 1,
                        # Missing 'role'
                        "content": "Test message",
                    }
                ]
            )
        assert "role" in excinfo.value.details.get("field", "")

        # Test with invalid role
        with pytest.raises(ValidationError) as excinfo:
            service.create_bulk_messages(
                [
                    {
                        "chat_session_id": 1,
                        "role": "invalid_role",  # Invalid role
                        "content": "Test message",
                    }
                ]
            )
        assert "role" in excinfo.value.details

        # Test with empty content
        with pytest.raises(ValidationError) as excinfo:
            service.create_bulk_messages(
                [
                    {
                        "chat_session_id": 1,
                        "role": "user",
                        "content": "",  # Empty content
                    }
                ]
            )
        assert "content" in excinfo.value.details

        # Verify repository methods were not called
        mock_message_repository.create_bulk.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()

    def test_update_message(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test updating a message."""
        # Setup
        mock_message_repository.get_by_id.return_value = sample_message

        updated_message = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Updated content",  # Changed
        )
        mock_message_repository.update.return_value = updated_message

        # Execute
        result = service.update_message(
            message_id=1,
            content="Updated content",
        )

        # Verify
        assert result == updated_message
        mock_message_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.update.assert_called_once_with(
            1, content="Updated content"
        )
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_update_message_empty_content(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test updating a message with empty content."""
        # Setup
        mock_message_repository.get_by_id.return_value = sample_message

        # Execute and verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_message(
                message_id=1,
                content="",  # Empty content
            )

        assert "content" in excinfo.value.details
        mock_message_repository.update.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()

    def test_update_message_not_found(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test updating a non-existent message."""
        # Setup
        mock_message_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_message(
                message_id=999,
                content="Updated content",
            )

        # Verify repository methods were not called
        mock_message_repository.update.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()

    def test_delete_message(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test deleting a message and all subsequent messages."""
        # Setup
        mock_message_repository.get_by_id.return_value = sample_message
        mock_message_repository.delete_message_and_subsequent.return_value = (
            3  # 3 messages deleted
        )

        # Execute
        deleted_count = service.delete_message(1)

        # Verify
        assert deleted_count == 3
        mock_message_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.delete_message_and_subsequent.assert_called_once_with(1)
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_delete_message_single(
        self,
        service,
        mock_message_repository,
        mock_chat_session_repository,
        sample_message,
    ):
        """Test deleting a message when it's the last message in conversation."""
        # Setup
        mock_message_repository.get_by_id.return_value = sample_message
        mock_message_repository.delete_message_and_subsequent.return_value = (
            1  # Only 1 message deleted
        )

        # Execute
        deleted_count = service.delete_message(1)

        # Verify
        assert deleted_count == 1
        mock_message_repository.get_by_id.assert_called_once_with(1)
        mock_message_repository.delete_message_and_subsequent.assert_called_once_with(1)
        mock_chat_session_repository.update_session_timestamp.assert_called_once_with(1)

    def test_delete_message_not_found(
        self, service, mock_message_repository, mock_chat_session_repository
    ):
        """Test deleting a non-existent message."""
        # Setup
        mock_message_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.delete_message(999)

        # Verify repository methods were not called
        mock_message_repository.delete_message_and_subsequent.assert_not_called()
        mock_chat_session_repository.update_session_timestamp.assert_not_called()


class TestMessageServiceClaudeCodeIntegration:
    """Test the MessageService Claude Code integration functionality."""

    @pytest.fixture
    def mock_message_repository(self):
        """Create a mock message repository."""
        return MagicMock()

    @pytest.fixture
    def mock_chat_session_repository(self):
        """Create a mock chat session repository."""
        return MagicMock()

    @pytest.fixture
    def mock_claudecode_client(self):
        """Create a mock Claude Code client."""
        return MagicMock()

    @pytest.fixture
    def mock_settings_service(self):
        """Create a mock settings service."""
        return MagicMock()

    @pytest.fixture
    def claudecode_service(
        self,
        mock_message_repository,
        mock_chat_session_repository,
        mock_claudecode_client,
        mock_settings_service,
    ):
        """Create a MessageService with Claude Code client."""
        return MessageService(
            mock_message_repository,
            mock_chat_session_repository,
            settings_service=mock_settings_service,
            openrouter_client=None,
            claudecode_client=mock_claudecode_client,
        )

    @pytest.fixture
    def claudecode_chat_session(self):
        """Create a mock chat session with ClaudeCode AI model."""
        ai_model = AIModel(id=1, label="ClaudeCode", description="Claude Code CLI")
        character = Character(
            id=1, 
            label="test_char", 
            name="Test Character",
            description="A test character"
        )
        user_profile = UserProfile(
            id=1,
            label="test_user",
            name="Test User", 
            description="A test user"
        )
        system_prompt = SystemPrompt(
            id=1,
            label="test_prompt",
            content="You are a helpful assistant."
        )
        
        chat_session = ChatSession(
            id=1,
            character_id=1,
            user_profile_id=1,
            ai_model_id=1,
            system_prompt_id=1,
            pre_prompt="Pre-prompt content",
            pre_prompt_enabled=True,
            post_prompt="Post-prompt content",
            post_prompt_enabled=True,
        )
        
        # Set up relationships
        chat_session.ai_model = ai_model
        chat_session.character = character
        chat_session.user_profile = user_profile
        chat_session.system_prompt = system_prompt
        
        return chat_session

    def test_generate_streaming_response_routes_to_claude_code(
        self,
        claudecode_service,
        mock_chat_session_repository,
        claudecode_chat_session,
    ):
        """Test that ClaudeCode model routes to Claude Code implementation."""
        # Setup
        mock_chat_session_repository.get_by_id_with_relations.return_value = claudecode_chat_session
        
        # Mock the Claude Code specific method
        with patch.object(claudecode_service, 'generate_streaming_response_claude_code') as mock_claude_method:
            mock_claude_method.return_value = iter([{"type": "content", "data": "test"}])
            
            # Execute
            result = list(claudecode_service.generate_streaming_response(1, "Hello"))
            
            # Verify Claude Code method was called
            mock_claude_method.assert_called_once_with(1, "Hello", None)
            assert result == [{"type": "content", "data": "test"}]

    def test_generate_streaming_response_claude_code_success(
        self,
        claudecode_service,
        mock_message_repository,
        mock_chat_session_repository,
        mock_claudecode_client,
        claudecode_chat_session,
    ):
        """Test successful Claude Code streaming response."""
        # Setup chat session
        mock_chat_session_repository.get_by_id_with_relations.return_value = claudecode_chat_session
        
        # Setup user message creation
        user_message = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Hello"
        )
        mock_message_repository.create.side_effect = [user_message]
        
        # Setup Claude Code streaming response
        mock_claudecode_client.chat_completion_stream.return_value = [
            {"type": "system", "message": "Starting Claude Code"},
            {"type": "assistant", "message": {"content": [{"text": "Hello! "}]}},
            {"type": "assistant", "message": {"content": [{"text": "How can I help you?"}]}},
            {"type": "result", "usage": {"input_tokens": 10, "output_tokens": 5}}
        ]
        
        # Setup AI message creation
        ai_message = Message(
            id=2,
            chat_session_id=1,
            role=MessageRole.ASSISTANT,
            content="Hello! How can I help you?"
        )
        mock_message_repository.create.side_effect = [user_message, ai_message]
        
        # Execute
        result = list(claudecode_service.generate_streaming_response_claude_code(1, "Hello"))
        
        # Verify
        expected_events = [
            {"type": "user_message_saved", "user_message_id": 1},
            {"type": "content", "data": "Hello! "},
            {"type": "content", "data": "How can I help you?"},
            {"type": "done", "ai_message_id": 2}
        ]
        
        assert result == expected_events
        
        # Verify Claude Code client was called with correct parameters
        mock_claudecode_client.chat_completion_stream.assert_called_once()
        call_args = mock_claudecode_client.chat_completion_stream.call_args
        assert "You are a helpful assistant." in call_args[1]["system_prompt"]
        assert "User: Hello" in call_args[1]["conversation_text"]

    def test_generate_streaming_response_claude_code_no_client(
        self,
        mock_message_repository,
        mock_chat_session_repository,
        mock_settings_service,
    ):
        """Test Claude Code streaming when client is not available."""
        # Setup service without Claude Code client
        service = MessageService(
            mock_message_repository,
            mock_chat_session_repository,
            settings_service=mock_settings_service,
            openrouter_client=None,
            claudecode_client=None,
        )
        
        # Execute and verify exception
        with pytest.raises(BusinessRuleError, match="Claude Code client not available"):
            list(service.generate_streaming_response_claude_code(1, "Hello"))

    def test_generate_streaming_response_claude_code_error_handling(
        self,
        claudecode_service,
        mock_message_repository,
        mock_chat_session_repository,
        mock_claudecode_client,
        claudecode_chat_session,
    ):
        """Test Claude Code streaming error handling."""
        # Setup chat session
        mock_chat_session_repository.get_by_id_with_relations.return_value = claudecode_chat_session
        
        # Setup user message creation
        user_message = Message(
            id=1,
            chat_session_id=1,
            role=MessageRole.USER,
            content="Hello"
        )
        mock_message_repository.create.side_effect = [user_message]
        
        # Setup Claude Code client to raise exception
        mock_claudecode_client.chat_completion_stream.side_effect = Exception("Claude Code failed")
        
        # Execute
        result = list(claudecode_service.generate_streaming_response_claude_code(1, "Hello"))
        
        # Verify error event
        assert any(event.get("type") == "error" for event in result)
        assert any("Claude Code failed" in str(event.get("error", "")) for event in result)

    def test_format_conversation_for_claude_code(
        self,
        claudecode_service,
        mock_message_repository,
    ):
        """Test conversation formatting for Claude Code CLI."""
        # Setup historical messages
        history = [
            Message(id=1, chat_session_id=1, role=MessageRole.USER, content="First message"),
            Message(id=2, chat_session_id=1, role=MessageRole.ASSISTANT, content="First response"),
            Message(id=3, chat_session_id=1, role=MessageRole.USER, content="Second message"),
        ]
        mock_message_repository.get_by_chat_session_id.return_value = history
        
        # Execute
        result = claudecode_service.format_conversation_for_claude_code(1, "New message")
        
        # Verify
        expected = (
            "User: First message\n"
            "Assistant: First response\n"
            "User: Second message\n"
            "User: New message"
        )
        
        assert result == expected

    def test_build_system_prompt_with_claude_code_session(
        self,
        claudecode_service,
        claudecode_chat_session,
    ):
        """Test system prompt building for Claude Code session."""
        # Execute
        result = claudecode_service.build_system_prompt(claudecode_chat_session)
        
        # Verify all components are included
        assert "Pre-prompt content" in result
        assert "You are a helpful assistant." in result
        assert "A test character" in result
        assert "A test user" in result
        assert "---" in result  # Separator
