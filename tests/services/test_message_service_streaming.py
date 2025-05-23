"""Tests for streaming-related MessageService methods."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.models.chat_session import ChatSession
from app.models.message import MessageRole
from app.services.message_service import MessageService
from app.utils.exceptions import BusinessRuleError


class TestBuildSystemPrompt:
    """Test cases for build_system_prompt method."""

    def test_build_system_prompt_all_fields(self):
        """Test building system prompt with all fields present."""
        # Create mock chat session with all fields
        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = True
        chat_session.pre_prompt = "Remember to stay in character"
        chat_session.system_prompt = Mock(content="You are a helpful AI assistant")
        chat_session.character = Mock(description="A friendly robot named Bob")
        chat_session.user_profile = Mock(
            description="A curious student learning Python"
        )

        # Create service
        service = MessageService(Mock(), Mock())

        # Build prompt
        result = service.build_system_prompt(chat_session)

        # Verify result
        expected = (
            "Remember to stay in character\n"
            "---\n"
            "You are a helpful AI assistant\n"
            "---\n"
            "A friendly robot named Bob\n"
            "---\n"
            "A curious student learning Python"
        )
        assert result == expected

    def test_build_system_prompt_no_pre_prompt(self):
        """Test building system prompt without pre-prompt."""
        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = False
        chat_session.pre_prompt = "This should be ignored"
        chat_session.system_prompt = Mock(content="System prompt")
        chat_session.character = Mock(description="Character description")
        chat_session.user_profile = Mock(description="User description")

        service = MessageService(Mock(), Mock())
        result = service.build_system_prompt(chat_session)

        expected = (
            "System prompt\n"
            "---\n"
            "Character description\n"
            "---\n"
            "User description"
        )
        assert result == expected

    def test_build_system_prompt_missing_descriptions(self):
        """Test building system prompt with missing descriptions."""
        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = False
        chat_session.system_prompt = Mock(content="System prompt")
        chat_session.character = Mock(description=None)
        chat_session.user_profile = Mock(description=None)

        service = MessageService(Mock(), Mock())
        result = service.build_system_prompt(chat_session)

        expected = (
            "System prompt\n"
            "---\n"
            "No character description provided\n"
            "---\n"
            "No user description provided"
        )
        assert result == expected

    def test_build_system_prompt_with_whitespace(self):
        """Test that whitespace is properly stripped."""
        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = True
        chat_session.pre_prompt = "  Pre-prompt with spaces  \n"
        chat_session.system_prompt = Mock(content="\tSystem prompt with tabs\t")
        chat_session.character = Mock(description="  Character  ")
        chat_session.user_profile = Mock(description="User\n\n")

        service = MessageService(Mock(), Mock())
        result = service.build_system_prompt(chat_session)

        expected = (
            "Pre-prompt with spaces\n"
            "---\n"
            "System prompt with tabs\n"
            "---\n"
            "Character\n"
            "---\n"
            "User"
        )
        assert result == expected


class TestFormatMessagesForOpenRouter:
    """Test cases for format_messages_for_openrouter method."""

    def test_format_messages_basic(self, db_session):
        """Test basic message formatting."""
        # Mock repositories
        message_repo = Mock()
        chat_session_repo = Mock()

        # Mock chat session with relationships
        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = False
        chat_session.post_prompt_enabled = False
        chat_session.system_prompt = Mock(content="System prompt")
        chat_session.character = Mock(description="Character")
        chat_session.user_profile = Mock(description="User")

        chat_session_repo.get_by_id_with_relations.return_value = chat_session

        # Mock message history
        history = [
            Mock(role=MessageRole.USER, content="Hello"),
            Mock(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]
        message_repo.get_by_chat_session_id.return_value = history

        # Create service
        service = MessageService(message_repo, chat_session_repo)

        # Format messages
        result = service.format_messages_for_openrouter(1, "New message")

        # Verify result
        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert "System prompt" in result[0]["content"]
        assert result[1] == {"role": "user", "content": "Hello"}
        assert result[2] == {"role": "assistant", "content": "Hi there!"}
        assert result[3] == {"role": "user", "content": "New message"}

    def test_format_messages_with_post_prompt(self, db_session):
        """Test message formatting with post-prompt."""
        message_repo = Mock()
        chat_session_repo = Mock()

        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = False
        chat_session.post_prompt_enabled = True
        chat_session.post_prompt = "Remember to be concise"
        chat_session.system_prompt = Mock(content="System")
        chat_session.character = Mock(description="Char")
        chat_session.user_profile = Mock(description="User")

        chat_session_repo.get_by_id_with_relations.return_value = chat_session
        message_repo.get_by_chat_session_id.return_value = []

        service = MessageService(message_repo, chat_session_repo)
        result = service.format_messages_for_openrouter(1, "Message")

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1] == {"role": "system", "content": "Remember to be concise"}
        assert result[2] == {"role": "user", "content": "Message"}

    def test_format_messages_empty_history(self, db_session):
        """Test formatting with no message history."""
        message_repo = Mock()
        chat_session_repo = Mock()

        chat_session = Mock(spec=ChatSession)
        chat_session.pre_prompt_enabled = False
        chat_session.post_prompt_enabled = False
        chat_session.system_prompt = Mock(content="System")
        chat_session.character = Mock(description="Char")
        chat_session.user_profile = Mock(description="User")

        chat_session_repo.get_by_id_with_relations.return_value = chat_session
        message_repo.get_by_chat_session_id.return_value = []

        service = MessageService(message_repo, chat_session_repo)
        result = service.format_messages_for_openrouter(1, "First message")

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1] == {"role": "user", "content": "First message"}


class TestGenerateStreamingResponse:
    """Test cases for generate_streaming_response method."""

    @pytest.mark.asyncio
    async def test_streaming_response_success(self, db_session):
        """Test successful streaming response generation."""
        # Mock dependencies
        message_repo = Mock()
        chat_session_repo = Mock()
        settings_service = Mock()
        openrouter_client = AsyncMock()

        # Mock settings
        settings_service.get_openrouter_api_key.return_value = "test-api-key"

        # Mock chat session
        chat_session = Mock(spec=ChatSession)
        chat_session.ai_model = Mock(label="gpt-3.5-turbo")
        chat_session.pre_prompt_enabled = False
        chat_session.post_prompt_enabled = False
        chat_session.system_prompt = Mock(content="System")
        chat_session.character = Mock(description="Char")
        chat_session.user_profile = Mock(description="User")

        chat_session_repo.get_by_id_with_relations.return_value = chat_session
        message_repo.get_by_chat_session_id.return_value = []

        # Mock streaming response
        async def mock_stream():
            chunks = [
                {"choices": [{"delta": {"content": "Hello"}}]},
                {"choices": [{"delta": {"content": " world"}}]},
                {"choices": [{"delta": {"content": "!"}}]},
            ]
            for chunk in chunks:
                yield chunk

        # Make create_streaming_completion return the generator directly
        openrouter_client.create_streaming_completion = Mock(return_value=mock_stream())

        # Mock create_assistant_message
        message_repo.create = Mock(return_value=Mock(id=1))

        # Create service
        service = MessageService(
            message_repo,
            chat_session_repo,
            settings_service=settings_service,
            openrouter_client=openrouter_client,
        )

        # Collect streamed chunks
        chunks = []
        async for chunk in service.generate_streaming_response(1, "Test", 1):
            chunks.append(chunk)

        # Verify
        assert chunks == ["Hello", " world", "!"]
        assert message_repo.create.called
        saved_message = message_repo.create.call_args[1]
        assert saved_message["content"] == "Hello world!"
        assert saved_message["role"] == MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_streaming_response_no_api_key(self):
        """Test streaming response with missing API key."""
        settings_service = Mock()
        settings_service.get_openrouter_api_key.return_value = None

        service = MessageService(
            Mock(), Mock(), settings_service=settings_service, openrouter_client=Mock()
        )

        with pytest.raises(
            BusinessRuleError, match="OpenRouter API key not configured"
        ):
            async for _ in service.generate_streaming_response(1, "Test", 1):
                pass

    @pytest.mark.asyncio
    async def test_streaming_response_no_ai_model(self):
        """Test streaming response with missing AI model."""
        settings_service = Mock()
        settings_service.get_openrouter_api_key.return_value = "key"

        chat_session_repo = Mock()
        chat_session = Mock(spec=ChatSession)
        chat_session.ai_model = None
        chat_session_repo.get_by_id_with_relations.return_value = chat_session

        service = MessageService(
            Mock(),
            chat_session_repo,
            settings_service=settings_service,
            openrouter_client=Mock(),
        )

        with pytest.raises(BusinessRuleError, match="AI model not configured"):
            async for _ in service.generate_streaming_response(1, "Test", 1):
                pass

    @pytest.mark.asyncio
    async def test_streaming_response_error_handling(self):
        """Test error handling during streaming."""
        # Mock dependencies
        message_repo = Mock()
        chat_session_repo = Mock()
        settings_service = Mock()
        openrouter_client = AsyncMock()

        settings_service.get_openrouter_api_key.return_value = "key"

        chat_session = Mock(spec=ChatSession)
        chat_session.ai_model = Mock(label="gpt-3.5-turbo")
        chat_session.pre_prompt_enabled = False
        chat_session.post_prompt_enabled = False
        chat_session.system_prompt = Mock(content="System")
        chat_session.character = Mock(description="Char")
        chat_session.user_profile = Mock(description="User")

        chat_session_repo.get_by_id_with_relations.return_value = chat_session
        message_repo.get_by_chat_session_id.return_value = []

        # Mock streaming that raises error after some chunks
        async def mock_stream():
            yield {"choices": [{"delta": {"content": "Partial"}}]}
            raise Exception("Stream error")

        # Make create_streaming_completion return the generator directly
        openrouter_client.create_streaming_completion = Mock(return_value=mock_stream())
        message_repo.create = Mock(return_value=Mock(id=1))

        service = MessageService(
            message_repo,
            chat_session_repo,
            settings_service=settings_service,
            openrouter_client=openrouter_client,
        )

        # Collect chunks and expect error
        chunks = []
        with pytest.raises(Exception, match="Stream error"):
            async for chunk in service.generate_streaming_response(1, "Test", 1):
                chunks.append(chunk)

        # Verify partial response was saved with error message
        assert chunks == ["Partial"]
        assert message_repo.create.called
        saved_message = message_repo.create.call_args[1]
        assert "Partial" in saved_message["content"]
        assert "[Response interrupted due to error]" in saved_message["content"]
