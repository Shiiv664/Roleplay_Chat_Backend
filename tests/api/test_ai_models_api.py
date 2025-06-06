"""Tests for the AI Models API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.ai_model import AIModel
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_ai_model_service():
    """Create a mock for the AIModelService."""
    with patch("app.api.namespaces.ai_models.AIModelService") as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_ai_model_data():
    """Sample AI model data for testing."""
    return {
        "id": 1,
        "label": "test_model",
        "description": "A test AI model description",
        "created_at": "2023-05-18T12:00:00",
        "updated_at": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_ai_model(sample_ai_model_data):
    """Create a sample AI model object from sample data."""
    model = AIModel(
        id=sample_ai_model_data["id"],
        label=sample_ai_model_data["label"],
        description=sample_ai_model_data["description"],
    )
    return model


class TestAIModelsAPI:
    """Test the AI Models API endpoints."""

    def test_get_ai_models_list(self, client, mock_ai_model_service, sample_ai_model):
        """Test getting a list of AI models."""
        # Configure the mock
        mock_ai_model_service.get_all_models.return_value = [sample_ai_model]

        # Execute API request
        response = client.get("/api/v1/ai-models/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_ai_model.id
        assert data["data"][0]["label"] == sample_ai_model.label
        assert data["data"][0]["description"] == sample_ai_model.description

        # Verify service was called
        mock_ai_model_service.get_all_models.assert_called_once()

    def test_get_ai_model_by_id(self, client, mock_ai_model_service, sample_ai_model):
        """Test getting an AI model by ID."""
        # Configure the mock
        mock_ai_model_service.get_model.return_value = sample_ai_model

        # Execute API request
        response = client.get(f"/api/v1/ai-models/{sample_ai_model.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_ai_model.id
        assert data["data"]["label"] == sample_ai_model.label
        assert data["data"]["description"] == sample_ai_model.description

        # Verify service was called with correct ID
        mock_ai_model_service.get_model.assert_called_once_with(sample_ai_model.id)

    def test_get_ai_model_not_found(self, client, mock_ai_model_service):
        """Test getting a non-existent AI model."""
        # Configure the mock to raise an exception
        mock_ai_model_service.get_model.side_effect = ResourceNotFoundError(
            "AI model with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/ai-models/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_ai_model_service.get_model.assert_called_once_with(999)

    def test_create_ai_model(self, client, mock_ai_model_service, sample_ai_model):
        """Test creating a new AI model."""
        # Data to send in request
        model_data = {"label": "new_model", "description": "A new AI model for testing"}

        # Configure the mock
        mock_ai_model_service.create_model.return_value = sample_ai_model

        # Execute API request
        response = client.post(
            "/api/v1/ai-models/",
            data=json.dumps(model_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_ai_model.id

        # Verify service was called with correct arguments
        mock_ai_model_service.create_model.assert_called_once_with(
            label="new_model", description="A new AI model for testing"
        )

    def test_create_ai_model_validation_error(self, client, mock_ai_model_service):
        """Test validation error when creating an AI model."""
        # Missing required 'label' field
        model_data = {"description": "This should fail validation"}

        # Configure the mock to raise validation error
        error_details = {"label": "AI model label is required"}
        mock_ai_model_service.create_model.side_effect = ValidationError(
            "AI model validation failed", details=error_details
        )

        # Execute API request
        response = client.post(
            "/api/v1/ai-models/",
            data=json.dumps(model_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["label"] == "AI model label is required"

    def test_update_ai_model(self, client, mock_ai_model_service, sample_ai_model):
        """Test updating an AI model."""
        # Data to send in update request
        update_data = {"description": "Updated description"}

        # Create an updated model based on the sample
        updated_model = AIModel(
            id=sample_ai_model.id,
            label=sample_ai_model.label,
            description="Updated description",
        )

        # Configure the mock
        mock_ai_model_service.update_model.return_value = updated_model

        # Execute API request
        response = client.put(
            f"/api/v1/ai-models/{sample_ai_model.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_ai_model.id
        assert data["data"]["description"] == "Updated description"

        # Verify service was called with correct arguments
        mock_ai_model_service.update_model.assert_called_once_with(
            model_id=sample_ai_model.id, description="Updated description", label=None
        )

    def test_update_ai_model_not_found(self, client, mock_ai_model_service):
        """Test updating a non-existent AI model."""
        # Data to send in update request
        update_data = {"description": "Updated description"}

        # Configure the mock to raise an exception
        mock_ai_model_service.update_model.side_effect = ResourceNotFoundError(
            "AI model with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/ai-models/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_ai_model(self, client, mock_ai_model_service, sample_ai_model):
        """Test deleting an AI model."""
        # Configure the mock
        # Note: delete_model does not return anything, so we don't need to configure a return value

        # Execute API request
        response = client.delete(f"/api/v1/ai-models/{sample_ai_model.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_ai_model.id
        assert "deleted" in data["data"]["message"].lower()

        # Verify service was called with correct ID
        mock_ai_model_service.delete_model.assert_called_once_with(sample_ai_model.id)

    def test_delete_ai_model_not_found(self, client, mock_ai_model_service):
        """Test deleting a non-existent AI model."""
        # Configure the mock to raise an exception
        mock_ai_model_service.delete_model.side_effect = ResourceNotFoundError(
            "AI model with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/ai-models/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_search_ai_models(self, client, mock_ai_model_service, sample_ai_model):
        """Test searching for AI models."""
        # Configure the mock
        mock_ai_model_service.search_models.return_value = [sample_ai_model]

        # Execute API request
        response = client.get("/api/v1/ai-models/search?query=test")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_ai_model.id
        assert data["data"][0]["label"] == sample_ai_model.label
        assert data["meta"]["query"] == "test"

        # Verify service was called with correct arguments
        mock_ai_model_service.search_models.assert_called_once_with("test")

    def test_search_ai_models_validation_error(self, client, mock_ai_model_service):
        """Test validation error when searching with a short query."""
        # Configure the mock to raise validation error
        mock_ai_model_service.search_models.side_effect = ValidationError(
            "Search query must be at least 2 characters"
        )

        # Execute API request with a single character query
        response = client.get("/api/v1/ai-models/search?query=a")

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_default_ai_model(self, client, mock_ai_model_service, sample_ai_model):
        """Test getting the default AI model."""
        # Configure the mock
        mock_ai_model_service.get_default_model.return_value = sample_ai_model

        # Execute API request
        response = client.get("/api/v1/ai-models/default")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_ai_model.id
        assert data["data"]["label"] == sample_ai_model.label

        # Verify service was called
        mock_ai_model_service.get_default_model.assert_called_once()

    def test_get_default_ai_model_not_found(self, client, mock_ai_model_service):
        """Test when no default AI model is set."""
        # Configure the mock to return None (no default model)
        mock_ai_model_service.get_default_model.return_value = None

        # Execute API request
        response = client.get("/api/v1/ai-models/default")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "no default ai model" in data["error"]["message"].lower()

        # Verify service was called
        mock_ai_model_service.get_default_model.assert_called_once()
