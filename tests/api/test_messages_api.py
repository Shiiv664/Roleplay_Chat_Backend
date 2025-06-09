"""Tests for the Messages API endpoints."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.message import Message, MessageRole
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_message_service():
    """Create a mock for the MessageService."""
    with patch("app.api.namespaces.messages.get_message_service") as mock_get_service:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the factory to return our mock
        mock_get_service.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_db_session_for_update_delete(mock_message_service):
    """Mock get_db_session for PUT/DELETE methods that create their own service instances."""
    with patch("app.utils.db.get_db_session") as mock_get_db_session:
        # Create a mock session
        mock_session = MagicMock()

        # Create a context manager that yields the mock session
        class MockSessionContext:
            def __enter__(self):
                return mock_session

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    mock_session.rollback.return_value = None
                else:
                    mock_session.commit.return_value = None
                mock_session.close.return_value = None

        mock_get_db_session.return_value = MockSessionContext()

        # Mock the repositories and service creation within the session context
        with patch(
            "app.repositories.message_repository.MessageRepository"
        ) as mock_message_repo_class:
            with patch(
                "app.repositories.chat_session_repository.ChatSessionRepository"
            ) as mock_chat_repo_class:
                with patch(
                    "app.repositories.application_settings_repository.ApplicationSettingsRepository"
                ):
                    with patch(
                        "app.repositories.ai_model_repository.AIModelRepository"
                    ):
                        with patch(
                            "app.repositories.system_prompt_repository.SystemPromptRepository"
                        ):
                            with patch(
                                "app.repositories.user_profile_repository.UserProfileRepository"
                            ):
                                with patch(
                                    "app.services.application_settings_service.ApplicationSettingsService"
                                ) as mock_settings_service_class:
                                    with patch(
                                        "app.services.message_service.MessageService"
                                    ) as mock_message_service_class:

                                        # Configure repository mocks
                                        mock_message_repo = MagicMock()
                                        mock_chat_repo = MagicMock()
                                        mock_message_repo_class.return_value = (
                                            mock_message_repo
                                        )
                                        mock_chat_repo_class.return_value = (
                                            mock_chat_repo
                                        )

                                        # Configure service mocks
                                        mock_settings_service_instance = MagicMock()
                                        mock_settings_service_instance.get_openrouter_api_key.return_value = (
                                            "fake_key"
                                        )
                                        mock_settings_service_class.return_value = (
                                            mock_settings_service_instance
                                        )

                                        # Configure MessageService mock to delegate to the original mock_message_service
                                        mock_service_instance = MagicMock()
                                        mock_service_instance.update_message = (
                                            mock_message_service.update_message
                                        )
                                        mock_service_instance.delete_message = (
                                            mock_message_service.delete_message
                                        )
                                        mock_message_service_class.return_value = (
                                            mock_service_instance
                                        )

                                        yield mock_session


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "id": 1,
        "chat_session_id": 100,
        "role": "user",
        "content": "This is a test message",
        "timestamp": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_message(sample_message_data):
    """Create a sample message object from sample data."""
    message = Message(
        id=sample_message_data["id"],
        chat_session_id=sample_message_data["chat_session_id"],
        role=(
            MessageRole.USER
            if sample_message_data["role"] == "user"
            else MessageRole.ASSISTANT
        ),
        content=sample_message_data["content"],
        timestamp=datetime.fromisoformat(sample_message_data["timestamp"]),
    )
    return message


@pytest.fixture
def sample_messages():
    """Create a list of sample messages for testing."""
    messages = [
        Message(
            id=1,
            chat_session_id=100,
            role=MessageRole.USER,
            content="Hello!",
            timestamp=datetime.fromisoformat("2023-05-18T12:00:00"),
        ),
        Message(
            id=2,
            chat_session_id=100,
            role=MessageRole.ASSISTANT,
            content="Hi there! How can I help you today?",
            timestamp=datetime.fromisoformat("2023-05-18T12:01:00"),
        ),
        Message(
            id=3,
            chat_session_id=100,
            role=MessageRole.USER,
            content="I need some information about your services.",
            timestamp=datetime.fromisoformat("2023-05-18T12:02:00"),
        ),
    ]
    return messages


class TestMessagesAPI:
    """Test the Messages API endpoints."""

    def test_get_message_by_id(self, client, mock_message_service, sample_message):
        """Test getting a message by ID."""
        # Configure the mock
        mock_message_service.get_message.return_value = sample_message

        # Execute API request
        response = client.get(f"/api/v1/messages/{sample_message.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_message.id
        assert data["data"]["chat_session_id"] == sample_message.chat_session_id
        assert data["data"]["role"] == sample_message.role.value
        assert data["data"]["content"] == sample_message.content

        # Verify service was called with correct ID
        mock_message_service.get_message.assert_called_once_with(sample_message.id)

    def test_get_message_not_found(self, client, mock_message_service):
        """Test getting a non-existent message."""
        # Configure the mock to raise an exception
        mock_message_service.get_message.side_effect = ResourceNotFoundError(
            "Message with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/messages/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_message_service.get_message.assert_called_once_with(999)

    def test_update_message(
        self,
        client,
        mock_message_service,
        sample_message,
        mock_db_session_for_update_delete,
    ):
        """Test updating a message."""
        # New content for update
        new_content = "This is the updated message content."

        # Create updated message object with new content
        updated_message = Message(
            id=sample_message.id,
            chat_session_id=sample_message.chat_session_id,
            role=sample_message.role,
            content=new_content,
            timestamp=sample_message.timestamp,
        )

        # Configure the mock
        mock_message_service.update_message.return_value = updated_message

        # Execute API request
        response = client.put(
            f"/api/v1/messages/{sample_message.id}",
            data=json.dumps({"content": new_content}),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_message.id
        assert data["data"]["content"] == new_content

        # Verify service was called with correct arguments
        mock_message_service.update_message.assert_called_once_with(
            sample_message.id, new_content
        )

    def test_update_message_not_found(self, client, mock_message_service):
        """Test updating a non-existent message."""
        # Configure the mock to raise an exception
        mock_message_service.update_message.side_effect = ResourceNotFoundError(
            "Message with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/messages/999",
            data=json.dumps({"content": "New content"}),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_update_message_validation_error(
        self,
        client,
        mock_message_service,
        sample_message,
        mock_db_session_for_update_delete,
    ):
        """Test validation error when updating a message."""
        # Configure the mock to raise a validation error
        mock_message_service.update_message.side_effect = ValidationError(
            "Message content cannot be empty",
            details={"content": "Content must not be empty"},
        )

        # Execute API request with empty content
        response = client.put(
            f"/api/v1/messages/{sample_message.id}",
            data=json.dumps({"content": ""}),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["content"] == "Content must not be empty"

    def test_delete_message(
        self,
        client,
        mock_message_service,
        sample_message,
        mock_db_session_for_update_delete,
    ):
        """Test deleting a message."""
        # Configure the mock to return a count of deleted messages
        mock_message_service.delete_message.return_value = 3  # 3 messages deleted

        # Execute API request
        response = client.delete(f"/api/v1/messages/{sample_message.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "Successfully deleted 3 message(s)" == data["data"]["message"]
        assert data["data"]["deleted_count"] == 3

        # Verify service was called with correct ID
        mock_message_service.delete_message.assert_called_once_with(sample_message.id)

    def test_delete_message_not_found(self, client, mock_message_service):
        """Test deleting a non-existent message."""
        # Configure the mock to raise an exception
        mock_message_service.delete_message.side_effect = ResourceNotFoundError(
            "Message with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/messages/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_get_messages_by_chat_session(
        self, client, mock_message_service, sample_messages
    ):
        """Test getting messages for a chat session."""
        # Sample pagination data
        pagination = {
            "page": 1,
            "per_page": 10,
            "total_items": len(sample_messages),
            "total_pages": 1,
        }

        # Configure the mock
        mock_message_service.get_paged_messages.return_value = (
            sample_messages,
            pagination,
        )

        # Execute API request
        response = client.get("/api/v1/messages/chat-sessions/100")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]["items"]) == len(sample_messages)
        assert data["data"]["pagination"]["total_items"] == len(sample_messages)

        # Verify service was called with correct arguments
        mock_message_service.get_paged_messages.assert_called_once_with(100, 1, 50)

    def test_get_messages_chat_session_not_found(self, client, mock_message_service):
        """Test getting messages for a non-existent chat session."""
        # Configure the mock to raise an exception
        mock_message_service.get_paged_messages.side_effect = ResourceNotFoundError(
            "Chat session with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/messages/chat-sessions/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_create_message(self, client, mock_message_service, sample_message):
        """Test creating a new message."""
        # Data to send in request
        message_data = {"role": "assistant", "content": "This is a new test message"}

        # Create a new message object
        new_message = Message(
            id=2,
            chat_session_id=100,
            role=MessageRole.ASSISTANT,
            content=message_data["content"],
            timestamp=datetime.now(),
        )

        # Configure the mock
        mock_message_service.create_message.return_value = new_message

        # Execute API request
        response = client.post(
            "/api/v1/messages/chat-sessions/100",
            data=json.dumps(message_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["role"] == "assistant"
        assert data["data"]["content"] == message_data["content"]

        # Verify service was called with correct arguments
        mock_message_service.create_message.assert_called_once_with(
            100, "assistant", message_data["content"]
        )

    def test_create_message_validation_error(self, client, mock_message_service):
        """Test validation error when creating a message."""
        # Data with empty content
        message_data = {"role": "user", "content": ""}

        # Configure the mock to raise a validation error
        mock_message_service.create_message.side_effect = ValidationError(
            "Message content cannot be empty",
            details={"content": "Content must not be empty"},
        )

        # Execute API request
        response = client.post(
            "/api/v1/messages/chat-sessions/100",
            data=json.dumps(message_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["content"] == "Content must not be empty"

    def test_create_user_message_with_ai_response(self, client, mock_message_service):
        """Test creating a user message that also returns an AI response."""
        # User message content
        user_content = "Hello AI, how are you today?"

        # Create user and AI message objects
        user_message = Message(
            id=5,
            chat_session_id=100,
            role=MessageRole.USER,
            content=user_content,
            timestamp=datetime.now(),
        )

        ai_response = Message(
            id=6,
            chat_session_id=100,
            role=MessageRole.ASSISTANT,
            content="I'm doing well, thank you for asking! How can I assist you today?",
            timestamp=datetime.now(),
        )

        # Configure the mocks
        mock_message_service.create_user_message.return_value = user_message
        mock_message_service.create_assistant_message.return_value = ai_response

        # Execute API request
        response = client.post(
            "/api/v1/messages/chat-sessions/100/user-message",
            data=json.dumps({"content": user_content}),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["user_message"]["role"] == "user"
        assert data["data"]["user_message"]["content"] == user_content
        assert data["data"]["ai_message"]["role"] == "assistant"

        # Verify service was called with correct arguments
        mock_message_service.create_user_message.assert_called_once_with(
            100, user_content
        )
        mock_message_service.create_assistant_message.assert_called_once()

    def test_regenerate_ai_response(
        self, client, mock_message_service, sample_messages
    ):
        """Test regenerating an AI response."""
        # Find an assistant message in the sample messages
        assistant_message = next(
            (msg for msg in sample_messages if msg.role == MessageRole.ASSISTANT), None
        )

        # New AI response content
        new_response = "This is a regenerated AI response."

        # Create updated message with new content
        updated_message = Message(
            id=assistant_message.id,
            chat_session_id=assistant_message.chat_session_id,
            role=assistant_message.role,
            content=new_response,
            timestamp=assistant_message.timestamp,
        )

        # Configure the mocks
        mock_message_service.get_latest_messages.return_value = sample_messages
        mock_message_service.update_message.return_value = updated_message

        # Execute API request
        response = client.post("/api/v1/messages/chat-sessions/100/regenerate")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == assistant_message.id
        assert data["data"]["content"] == new_response

        # Verify service was called with correct arguments
        mock_message_service.get_latest_messages.assert_called_once_with(100, 10)
        mock_message_service.update_message.assert_called_once_with(
            assistant_message.id, mock_message_service.update_message.call_args[0][1]
        )

    def test_get_latest_messages(self, client, mock_message_service, sample_messages):
        """Test getting latest messages from a chat session."""
        # Configure the mock
        mock_message_service.get_latest_messages.return_value = sample_messages

        # Execute API request
        response = client.get("/api/v1/messages/chat-sessions/100/latest?count=5")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]["items"]) == len(sample_messages)

        # Verify message details are present
        for i, msg in enumerate(sample_messages):
            api_msg = data["data"]["items"][i]
            assert api_msg["id"] == msg.id
            assert api_msg["role"] == msg.role.value
            assert api_msg["content"] == msg.content

        # Verify service was called with correct arguments
        mock_message_service.get_latest_messages.assert_called_once_with(100, 5)
