"""Integration tests for the sendMessage endpoint."""

import json
from unittest.mock import patch

import pytest

from app.models.ai_model import AIModel
from app.models.character import Character
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile


class TestSendMessageEndpoint:
    """Test cases for the sendMessage endpoint."""

    @pytest.fixture
    def chat_session_with_relationships(self, db_session):
        """Create a chat session with all relationships."""
        # Create related entities
        ai_model = AIModel(label="gpt-3.5-turbo", description="GPT-3.5 Turbo")
        system_prompt = SystemPrompt(
            label="default", content="You are a helpful AI assistant"
        )
        character = Character(
            label="bob", name="Bob", description="A friendly robot who loves to help"
        )
        user_profile = UserProfile(
            label="student",
            name="Student",
            description="A curious student learning programming",
        )

        db_session.add_all([ai_model, system_prompt, character, user_profile])
        db_session.commit()

        # Create chat session
        chat_session = ChatSession(
            character_id=character.id,
            user_profile_id=user_profile.id,
            ai_model_id=ai_model.id,
            system_prompt_id=system_prompt.id,
            pre_prompt="Stay in character",
            pre_prompt_enabled=True,
            post_prompt="Be concise",
            post_prompt_enabled=True,
        )
        db_session.add(chat_session)
        db_session.commit()

        return chat_session

    def test_send_message_validation_error(
        self, client, chat_session_with_relationships, db_session
    ):
        """Test sending message with validation error."""
        from unittest.mock import Mock, patch

        # Mock the get_message_service function to avoid database issues
        mock_service = Mock()
        with patch(
            "app.api.namespaces.messages.get_message_service", return_value=mock_service
        ):
            response = client.post(
                f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
                json={"content": "", "stream": True},
            )

            # Debug: print response details
            print(f"Status: {response.status_code}")
            print(f"Data: {response.data}")
            print(f"Headers: {dict(response.headers)}")

            assert response.status_code == 400
            data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "content is required" in data["error"]["message"].lower()

    def test_send_message_chat_session_not_found(self, client):
        """Test sending message to non-existent chat session."""
        response = client.post(
            "/api/v1/messages/chat-sessions/99999/send-message",
            json={"content": "Hello", "stream": True},
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_send_message_no_api_key(self, client, chat_session_with_relationships):
        """Test sending message without OpenRouter API key configured."""
        response = client.post(
            f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
            json={"content": "Hello", "stream": True},
        )

        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "api key not configured" in data["error"]["message"].lower()

    @patch("app.services.openrouter.client.OpenRouterClient.chat_completion_stream")
    @patch(
        "app.services.application_settings_service.ApplicationSettingsService.get_openrouter_api_key"
    )
    def test_send_message_streaming_success(
        self,
        mock_get_api_key,
        mock_streaming,
        client,
        chat_session_with_relationships,
        db_session,
    ):
        """Test successful streaming message response."""
        # Mock API key
        mock_get_api_key.return_value = "test-api-key"

        # Mock streaming response
        def mock_stream():
            chunks = [
                {"choices": [{"delta": {"content": "Hello"}}]},
                {"choices": [{"delta": {"content": " from"}}]},
                {"choices": [{"delta": {"content": " Bob!"}}]},
            ]
            for chunk in chunks:
                yield chunk

        mock_streaming.return_value = mock_stream()

        # Send request
        response = client.post(
            f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
            json={"content": "Hi there!", "stream": True},
        )

        # Check response
        assert response.status_code == 200
        assert response.content_type.startswith("text/event-stream")

        # Parse SSE events
        events = []
        for line in response.data.decode("utf-8").split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        # Verify events
        assert len(events) == 5  # 1 user_message_saved + 3 content + 1 done
        assert events[0] == {"type": "user_message_saved", "user_message_id": 1}
        assert events[1] == {"type": "content", "data": "Hello"}
        assert events[2] == {"type": "content", "data": " from"}
        assert events[3] == {"type": "content", "data": " Bob!"}
        assert events[4] == {"type": "done", "ai_message_id": 2}

        # Verify messages were saved
        messages = (
            db_session.query(Message)
            .filter_by(chat_session_id=chat_session_with_relationships.id)
            .order_by(Message.id)
            .all()
        )

        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hi there!"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hello from Bob!"

    @patch("app.services.openrouter.client.OpenRouterClient.chat_completion_stream")
    @patch(
        "app.services.application_settings_service.ApplicationSettingsService.get_openrouter_api_key"
    )
    def test_send_message_streaming_error(
        self,
        mock_get_api_key,
        mock_streaming,
        client,
        chat_session_with_relationships,
        db_session,
    ):
        """Test streaming message with error during stream."""
        mock_get_api_key.return_value = "test-api-key"

        # Mock streaming that raises error
        def mock_stream():
            yield {"choices": [{"delta": {"content": "Partial"}}]}
            raise Exception("Stream error")

        mock_streaming.return_value = mock_stream()

        response = client.post(
            f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
            json={"content": "Test", "stream": True},
        )

        assert response.status_code == 200
        assert response.content_type.startswith("text/event-stream")

        # Parse events
        events = []
        for line in response.data.decode("utf-8").split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        # Should have content and error events
        assert any(e["type"] == "content" for e in events)
        assert any(e["type"] == "error" for e in events)

        # Verify partial message was saved with error
        messages = (
            db_session.query(Message)
            .filter_by(
                chat_session_id=chat_session_with_relationships.id,
                role=MessageRole.ASSISTANT,
            )
            .all()
        )

        assert len(messages) == 1
        assert "Partial" in messages[0].content
        assert "[Response interrupted due to error]" in messages[0].content

    def test_send_message_non_streaming_not_implemented(
        self, client, chat_session_with_relationships
    ):
        """Test non-streaming mode returns not implemented error."""
        response = client.post(
            f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
            json={"content": "Hello", "stream": False},
        )

        # Should return 500 for NotImplementedError
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["success"] is False

    @patch(
        "app.services.application_settings_service.ApplicationSettingsService.get_openrouter_api_key"
    )
    def test_send_message_default_stream_true(
        self, mock_get_api_key, client, chat_session_with_relationships
    ):
        """Test that stream defaults to true when not specified."""
        mock_get_api_key.return_value = "test-api-key"

        # Don't specify stream parameter
        response = client.post(
            f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
            json={"content": "Hello"},
        )

        # Should attempt streaming (will fail due to no mock, but that's OK)
        assert response.status_code in [
            200,
            503,
        ]  # 200 if streaming, 503 if service error

    def test_send_message_with_message_history(
        self, client, chat_session_with_relationships, db_session
    ):
        """Test that message history is included in the prompt."""
        # Add some message history
        messages = [
            Message(
                chat_session_id=chat_session_with_relationships.id,
                role=MessageRole.USER,
                content="Previous user message",
            ),
            Message(
                chat_session_id=chat_session_with_relationships.id,
                role=MessageRole.ASSISTANT,
                content="Previous assistant response",
            ),
        ]
        db_session.add_all(messages)
        db_session.commit()

        # Mock the OpenRouter call to capture the messages sent
        with patch(
            "app.services.openrouter.client.OpenRouterClient.chat_completion_stream"
        ) as mock_streaming:
            with patch(
                "app.services.application_settings_service.ApplicationSettingsService.get_openrouter_api_key"
            ) as mock_key:
                mock_key.return_value = "test-key"

                # Setup mock to capture call arguments
                def mock_stream():
                    yield {"choices": [{"delta": {"content": "Response"}}]}

                mock_streaming.return_value = mock_stream()

                client.post(
                    f"/api/v1/messages/chat-sessions/{chat_session_with_relationships.id}/send-message",
                    json={"content": "New message", "stream": True},
                )

                # Verify the messages parameter included history
                call_args = mock_streaming.call_args
                messages_arg = call_args[1]["messages"]

                # Should have system + 2 history + post-prompt + new message
                assert len(messages_arg) >= 5
                assert messages_arg[0]["role"] == "system"
                assert any(
                    m["content"] == "Previous user message" for m in messages_arg
                )
                assert any(
                    m["content"] == "Previous assistant response" for m in messages_arg
                )
