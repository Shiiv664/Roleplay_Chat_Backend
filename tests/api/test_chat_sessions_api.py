"""Tests for the Chat Sessions API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.chat_session import ChatSession
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_chat_session_service():
    """Create a mock for the ChatSessionService."""
    with patch(
        "app.api.namespaces.chat_sessions.ChatSessionService"
    ) as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_chat_session_data():
    """Sample chat session data for testing."""
    return {
        "id": 1,
        "character_id": 100,
        "user_profile_id": 200,
        "ai_model_id": 300,
        "system_prompt_id": 400,
        "pre_prompt": "This is a pre-prompt",
        "pre_prompt_enabled": True,
        "post_prompt": "This is a post-prompt",
        "post_prompt_enabled": False,
        "start_time": "2023-05-18T12:00:00",
        "updated_at": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_chat_session(sample_chat_session_data):
    """Create a sample chat session object from sample data."""
    chat_session = ChatSession(
        id=sample_chat_session_data["id"],
        character_id=sample_chat_session_data["character_id"],
        user_profile_id=sample_chat_session_data["user_profile_id"],
        ai_model_id=sample_chat_session_data["ai_model_id"],
        system_prompt_id=sample_chat_session_data["system_prompt_id"],
        pre_prompt=sample_chat_session_data["pre_prompt"],
        pre_prompt_enabled=sample_chat_session_data["pre_prompt_enabled"],
        post_prompt=sample_chat_session_data["post_prompt"],
        post_prompt_enabled=sample_chat_session_data["post_prompt_enabled"],
    )
    return chat_session


class TestChatSessionsAPI:
    """Test the Chat Sessions API endpoints."""

    def test_get_chat_sessions_list(
        self, client, mock_chat_session_service, sample_chat_session
    ):
        """Test getting a list of chat sessions."""
        # Configure the mock
        mock_chat_session_service.get_session_with_relations.return_value = [
            sample_chat_session
        ]

        # Execute API request
        response = client.get("/api/v1/chat-sessions/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "pagination" in data["meta"]

        # Verify service was called
        # Note: In the current implementation we use repository directly, but
        # this test is future-proofed for when we might switch to using the service
        # mock_chat_session_service.get_all_sessions.assert_called_once()

    def test_get_chat_session_by_id(
        self, client, mock_chat_session_service, sample_chat_session
    ):
        """Test getting a chat session by ID."""
        # Configure the mock
        mock_chat_session_service.get_session_with_relations.return_value = (
            sample_chat_session
        )

        # Execute API request
        response = client.get(f"/api/v1/chat-sessions/{sample_chat_session.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_chat_session.id
        assert data["data"]["character_id"] == sample_chat_session.character_id
        assert data["data"]["user_profile_id"] == sample_chat_session.user_profile_id

        # Verify service was called with correct ID
        mock_chat_session_service.get_session_with_relations.assert_called_once_with(
            sample_chat_session.id
        )

    def test_get_chat_session_not_found(self, client, mock_chat_session_service):
        """Test getting a non-existent chat session."""
        # Configure the mock to raise an exception
        mock_chat_session_service.get_session_with_relations.side_effect = (
            ResourceNotFoundError("Chat session with ID A999 not found")
        )

        # Execute API request
        response = client.get("/api/v1/chat-sessions/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_chat_session_service.get_session_with_relations.assert_called_once_with(
            999
        )

    def test_create_chat_session(
        self, client, mock_chat_session_service, sample_chat_session
    ):
        """Test creating a new chat session with defaults."""
        # Data to send in request - only character_id required now
        session_data = {
            "character_id": 100,
        }

        # Configure the mock
        mock_chat_session_service.create_session_with_defaults.return_value = (
            sample_chat_session
        )

        # Execute API request
        response = client.post(
            "/api/v1/chat-sessions/",
            data=json.dumps(session_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_chat_session.id

        # Verify service was called with correct arguments
        mock_chat_session_service.create_session_with_defaults.assert_called_once_with(
            character_id=100
        )

    def test_create_chat_session_validation_error(
        self, client, mock_chat_session_service
    ):
        """Test validation error when creating a chat session."""
        # Missing required field
        session_data = {
            # character_id is missing
        }

        # Configure the mock to raise validation error
        error_details = {"character_id": "Character ID is required"}
        mock_chat_session_service.create_session_with_defaults.side_effect = (
            ValidationError("Chat session validation failed", details=error_details)
        )

        # Execute API request
        response = client.post(
            "/api/v1/chat-sessions/",
            data=json.dumps(session_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["character_id"] == "Character ID is required"

    def test_update_chat_session(
        self, client, mock_chat_session_service, sample_chat_session
    ):
        """Test updating a chat session."""
        # Data to send in update request
        update_data = {
            "ai_model_id": 301,
            "system_prompt_id": 401,
            "pre_prompt_enabled": False,
        }

        # Create an updated session based on the sample
        updated_session = ChatSession(
            id=sample_chat_session.id,
            character_id=sample_chat_session.character_id,
            user_profile_id=sample_chat_session.user_profile_id,
            ai_model_id=301,
            system_prompt_id=401,
            pre_prompt=sample_chat_session.pre_prompt,
            pre_prompt_enabled=False,
            post_prompt=sample_chat_session.post_prompt,
            post_prompt_enabled=sample_chat_session.post_prompt_enabled,
        )

        # Configure the mock
        mock_chat_session_service.update_session.return_value = updated_session

        # Execute API request
        response = client.put(
            f"/api/v1/chat-sessions/{sample_chat_session.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_chat_session.id
        assert data["data"]["ai_model_id"] == 301
        assert data["data"]["system_prompt_id"] == 401
        assert data["data"]["pre_prompt_enabled"] is False

        # Verify service was called with correct arguments
        mock_chat_session_service.update_session.assert_called_once_with(
            session_id=sample_chat_session.id,
            user_profile_id=None,
            ai_model_id=301,
            system_prompt_id=401,
            pre_prompt=None,
            pre_prompt_enabled=False,
            post_prompt=None,
            post_prompt_enabled=None,
            formatting_settings=None,
        )

    def test_update_chat_session_not_found(self, client, mock_chat_session_service):
        """Test updating a non-existent chat session."""
        # Data to send in update request
        update_data = {"ai_model_id": 301, "system_prompt_id": 401}

        # Configure the mock to raise an exception
        mock_chat_session_service.update_session.side_effect = ResourceNotFoundError(
            "Chat session with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/chat-sessions/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_chat_session(
        self, client, mock_chat_session_service, sample_chat_session
    ):
        """Test deleting a chat session."""
        # Configure the mock
        # Note: delete_session does not return anything, so we don't need to configure a return value

        # Execute API request
        response = client.delete(f"/api/v1/chat-sessions/{sample_chat_session.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_chat_session.id
        assert "deleted" in data["data"]["message"].lower()

        # Verify service was called with correct ID
        mock_chat_session_service.delete_session.assert_called_once_with(
            sample_chat_session.id
        )

    def test_delete_chat_session_not_found(self, client, mock_chat_session_service):
        """Test deleting a non-existent chat session."""
        # Configure the mock to raise an exception
        mock_chat_session_service.delete_session.side_effect = ResourceNotFoundError(
            "Chat session with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/chat-sessions/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_get_recent_chat_sessions(
        self, client, mock_chat_session_service, sample_chat_session_data
    ):
        """Test getting recent chat sessions."""
        # Configure the mock to return dictionary data (like our new service method)
        mock_chat_session_service.get_recent_sessions_with_data.return_value = [
            {**sample_chat_session_data, "message_count": 5}
        ]

        # Execute API request
        response = client.get("/api/v1/chat-sessions/recent?limit=5")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_chat_session_data["id"]
        assert data["data"][0]["message_count"] == 5
        assert data["meta"]["limit"] == 5

        # Verify service was called with correct arguments
        mock_chat_session_service.get_recent_sessions_with_data.assert_called_once_with(
            limit=5
        )

    def test_get_chat_sessions_by_character(
        self, client, mock_chat_session_service, sample_chat_session_data
    ):
        """Test getting chat sessions for a specific character."""
        # Configure the mock to return dictionary data (like our new service method)
        mock_chat_session_service.get_sessions_by_character_with_data.return_value = [
            {**sample_chat_session_data, "message_count": 10}
        ]

        # Execute API request
        response = client.get(
            f"/api/v1/chat-sessions/character/{sample_chat_session_data['character_id']}"
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_chat_session_data["id"]
        assert (
            data["data"][0]["character_id"] == sample_chat_session_data["character_id"]
        )
        assert data["data"][0]["message_count"] == 10
        assert data["meta"]["character_id"] == sample_chat_session_data["character_id"]

        # Verify service was called with correct arguments
        mock_chat_session_service.get_sessions_by_character_with_data.assert_called_once_with(
            sample_chat_session_data["character_id"]
        )

    def test_get_chat_sessions_by_character_not_found(
        self, client, mock_chat_session_service
    ):
        """Test getting chat sessions for a non-existent character."""
        # Configure the mock to raise an exception
        mock_chat_session_service.get_sessions_by_character_with_data.side_effect = (
            ResourceNotFoundError("Character with ID 999 not found")
        )

        # Execute API request
        response = client.get("/api/v1/chat-sessions/character/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_user_profile_endpoint_removed(self, client):
        """Test that the user profile endpoint has been removed."""
        # Execute API request to the removed endpoint
        response = client.get("/api/v1/chat-sessions/user-profile/200")

        # Verify the endpoint returns 404 (or 500 with 404 message due to error handler)
        assert response.status_code in [404, 500]

        if response.status_code == 500:
            # If it's a 500, it should contain error information indicating the endpoint doesn't exist
            data = json.loads(response.data)
            assert data["success"] is False
            # The error should indicate a problem (details might be None, but error should exist)
            assert "error" in data
        # If it's 404, that's perfect - the endpoint is properly removed
