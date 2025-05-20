"""Tests for the System Prompts API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.system_prompt import SystemPrompt
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_system_prompt_service():
    """Create a mock for the SystemPromptService."""
    with patch(
        "app.api.namespaces.system_prompts.SystemPromptService"
    ) as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_system_prompt_data():
    """Sample system prompt data for testing."""
    return {
        "id": 1,
        "label": "test_prompt",
        "content": "This is a test system prompt content.",
        "created_at": "2023-05-18T12:00:00",
        "updated_at": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_system_prompt(sample_system_prompt_data):
    """Create a sample system prompt object from sample data."""
    prompt = SystemPrompt(
        id=sample_system_prompt_data["id"],
        label=sample_system_prompt_data["label"],
        content=sample_system_prompt_data["content"],
    )
    return prompt


class TestSystemPromptsAPI:
    """Test the System Prompts API endpoints."""

    def test_get_system_prompts_list(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test getting a list of system prompts."""
        # Configure the mock
        mock_system_prompt_service.get_all_prompts.return_value = [sample_system_prompt]

        # Execute API request
        response = client.get("/api/v1/system-prompts/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_system_prompt.id
        assert data["data"][0]["label"] == sample_system_prompt.label
        assert data["data"][0]["content"] == sample_system_prompt.content

        # Verify service was called
        mock_system_prompt_service.get_all_prompts.assert_called_once()

    def test_get_system_prompt_by_id(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test getting a system prompt by ID."""
        # Configure the mock
        mock_system_prompt_service.get_prompt.return_value = sample_system_prompt

        # Execute API request
        response = client.get(f"/api/v1/system-prompts/{sample_system_prompt.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_system_prompt.id
        assert data["data"]["label"] == sample_system_prompt.label
        assert data["data"]["content"] == sample_system_prompt.content

        # Verify service was called with correct ID
        mock_system_prompt_service.get_prompt.assert_called_once_with(
            sample_system_prompt.id
        )

    def test_get_system_prompt_not_found(self, client, mock_system_prompt_service):
        """Test getting a non-existent system prompt."""
        # Configure the mock to raise an exception
        mock_system_prompt_service.get_prompt.side_effect = ResourceNotFoundError(
            "System prompt with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/system-prompts/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_system_prompt_service.get_prompt.assert_called_once_with(999)

    def test_create_system_prompt(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test creating a new system prompt."""
        # Data to send in request
        prompt_data = {
            "label": "new_prompt",
            "content": "This is a new system prompt for testing.",
        }

        # Configure the mock
        mock_system_prompt_service.create_prompt.return_value = sample_system_prompt

        # Execute API request
        response = client.post(
            "/api/v1/system-prompts/",
            data=json.dumps(prompt_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_system_prompt.id

        # Verify service was called with correct arguments
        mock_system_prompt_service.create_prompt.assert_called_once_with(
            label="new_prompt", content="This is a new system prompt for testing."
        )

    def test_create_system_prompt_validation_error(
        self, client, mock_system_prompt_service
    ):
        """Test validation error when creating a system prompt."""
        # Missing required 'content' field
        prompt_data = {"label": "invalid_prompt"}

        # Configure the mock to raise validation error
        error_details = {"content": "System prompt content is required"}
        mock_system_prompt_service.create_prompt.side_effect = ValidationError(
            "System prompt validation failed", details=error_details
        )

        # Execute API request
        response = client.post(
            "/api/v1/system-prompts/",
            data=json.dumps(prompt_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert (
            data["error"]["details"]["content"] == "System prompt content is required"
        )

    def test_update_system_prompt(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test updating a system prompt."""
        # Data to send in update request
        update_data = {"content": "Updated system prompt content."}

        # Create an updated prompt based on the sample
        updated_prompt = SystemPrompt(
            id=sample_system_prompt.id,
            label=sample_system_prompt.label,
            content="Updated system prompt content.",
        )

        # Configure the mock
        mock_system_prompt_service.update_prompt.return_value = updated_prompt

        # Execute API request
        response = client.put(
            f"/api/v1/system-prompts/{sample_system_prompt.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_system_prompt.id
        assert data["data"]["content"] == "Updated system prompt content."

        # Verify service was called with correct arguments
        mock_system_prompt_service.update_prompt.assert_called_once_with(
            prompt_id=sample_system_prompt.id,
            content="Updated system prompt content.",
            label=None,
        )

    def test_update_system_prompt_not_found(self, client, mock_system_prompt_service):
        """Test updating a non-existent system prompt."""
        # Data to send in update request
        update_data = {"content": "Updated system prompt content."}

        # Configure the mock to raise an exception
        mock_system_prompt_service.update_prompt.side_effect = ResourceNotFoundError(
            "System prompt with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/system-prompts/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_system_prompt(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test deleting a system prompt."""
        # Configure the mock
        # Note: delete_prompt does not return anything, so we don't need to configure a return value

        # Execute API request
        response = client.delete(f"/api/v1/system-prompts/{sample_system_prompt.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_system_prompt.id
        assert "deleted" in data["data"]["message"].lower()

        # Verify service was called with correct ID
        mock_system_prompt_service.delete_prompt.assert_called_once_with(
            sample_system_prompt.id
        )

    def test_delete_system_prompt_not_found(self, client, mock_system_prompt_service):
        """Test deleting a non-existent system prompt."""
        # Configure the mock to raise an exception
        mock_system_prompt_service.delete_prompt.side_effect = ResourceNotFoundError(
            "System prompt with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/system-prompts/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_search_system_prompts(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test searching for system prompts."""
        # Configure the mock
        mock_system_prompt_service.search_prompts.return_value = [sample_system_prompt]

        # Execute API request
        response = client.get("/api/v1/system-prompts/search?query=test")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_system_prompt.id
        assert data["data"][0]["label"] == sample_system_prompt.label
        assert data["meta"]["query"] == "test"

        # Verify service was called with correct arguments
        mock_system_prompt_service.search_prompts.assert_called_once_with("test")

    def test_search_system_prompts_validation_error(
        self, client, mock_system_prompt_service
    ):
        """Test validation error when searching with a short query."""
        # Configure the mock to raise validation error
        mock_system_prompt_service.search_prompts.side_effect = ValidationError(
            "Search query must be at least 2 characters"
        )

        # Execute API request with a single character query
        response = client.get("/api/v1/system-prompts/search?query=a")

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_default_system_prompt(
        self, client, mock_system_prompt_service, sample_system_prompt
    ):
        """Test getting the default system prompt."""
        # Configure the mock
        mock_system_prompt_service.get_default_prompt.return_value = (
            sample_system_prompt
        )

        # Execute API request
        response = client.get("/api/v1/system-prompts/default")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_system_prompt.id
        assert data["data"]["label"] == sample_system_prompt.label

        # Verify service was called
        mock_system_prompt_service.get_default_prompt.assert_called_once()

    def test_get_default_system_prompt_not_found(
        self, client, mock_system_prompt_service
    ):
        """Test when no default system prompt is set."""
        # Configure the mock to return None (no default prompt)
        mock_system_prompt_service.get_default_prompt.return_value = None

        # Execute API request
        response = client.get("/api/v1/system-prompts/default")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "no default system prompt" in data["error"]["message"].lower()

        # Verify service was called
        mock_system_prompt_service.get_default_prompt.assert_called_once()
