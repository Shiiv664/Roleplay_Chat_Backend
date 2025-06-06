"""Tests for OpenRouter API key endpoints in settings API."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.application_settings import ApplicationSettings
from app.utils.exceptions import ValidationError


@pytest.fixture
def mock_settings_service():
    """Create a mock for the ApplicationSettingsService."""
    with patch("app.api.namespaces.settings.get_settings_service") as mock_get_service:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        yield mock_service


class TestOpenRouterAPIKeyEndpoints:
    """Test OpenRouter API key management endpoints."""

    def test_get_openrouter_api_key_status_success(self, client, mock_settings_service):
        """Test getting API key status when key exists."""
        # Setup
        mock_settings_service.get_openrouter_api_key.return_value = "sk-or-test-key-123"

        # Execute
        response = client.get("/api/v1/settings/openrouter-api-key")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["has_api_key"] is True
        assert data["data"]["key_length"] == 18

    def test_get_openrouter_api_key_status_no_key(self, client, mock_settings_service):
        """Test getting API key status when no key exists."""
        # Setup
        mock_settings_service.get_openrouter_api_key.return_value = None

        # Execute
        response = client.get("/api/v1/settings/openrouter-api-key")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["has_api_key"] is False
        assert data["data"]["key_length"] == 0

    def test_get_openrouter_api_key_status_decryption_error(
        self, client, mock_settings_service
    ):
        """Test getting API key status when decryption fails."""
        # Setup
        mock_settings_service.get_openrouter_api_key.side_effect = ValidationError(
            "Failed to decrypt API key",
            details={"openrouter_api_key": "Decryption failed"},
        )

        # Execute
        response = client.get("/api/v1/settings/openrouter-api-key")

        # Verify
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Failed to decrypt API key" in data["error"]["message"]

    def test_set_openrouter_api_key_success(self, client, mock_settings_service):
        """Test successfully setting OpenRouter API key."""
        # Setup
        api_key = "sk-or-test-api-key-123456789"
        mock_settings_service.set_openrouter_api_key.return_value = ApplicationSettings(
            id=1
        )

        # Execute
        response = client.put(
            "/api/v1/settings/openrouter-api-key",
            data=json.dumps({"api_key": api_key}),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["message"] == "OpenRouter API key set successfully"
        mock_settings_service.set_openrouter_api_key.assert_called_once_with(api_key)

    def test_set_openrouter_api_key_missing_key(self, client, mock_settings_service):
        """Test setting API key without providing the key."""
        # Execute
        response = client.put(
            "/api/v1/settings/openrouter-api-key",
            data=json.dumps({}),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "API key is required" in data["error"]["message"]

    def test_set_openrouter_api_key_empty_key(self, client, mock_settings_service):
        """Test setting empty API key."""
        # Execute
        response = client.put(
            "/api/v1/settings/openrouter-api-key",
            data=json.dumps({"api_key": ""}),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "API key is required" in data["error"]["message"]

    def test_set_openrouter_api_key_validation_error(
        self, client, mock_settings_service
    ):
        """Test setting API key with validation error."""
        # Setup
        api_key = "invalid-key"
        mock_settings_service.set_openrouter_api_key.side_effect = ValidationError(
            "OpenRouter API key cannot be empty",
            details={"openrouter_api_key": "Must provide a valid API key"},
        )

        # Execute
        response = client.put(
            "/api/v1/settings/openrouter-api-key",
            data=json.dumps({"api_key": api_key}),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "OpenRouter API key cannot be empty" in data["error"]["message"]

    def test_set_openrouter_api_key_no_json_body(self, client, mock_settings_service):
        """Test setting API key without JSON body."""
        # Execute
        response = client.put("/api/v1/settings/openrouter-api-key")

        # Verify - Flask returns 415 for missing content-type
        assert response.status_code == 415
        data = json.loads(response.data)
        # Flask-RESTX returns a different format for 415 errors
        assert "message" in data
        assert "Content-Type" in data["message"]

    def test_clear_openrouter_api_key_success(self, client, mock_settings_service):
        """Test successfully clearing OpenRouter API key."""
        # Setup
        mock_settings_service.clear_openrouter_api_key.return_value = (
            ApplicationSettings(id=1)
        )

        # Execute
        response = client.delete("/api/v1/settings/openrouter-api-key")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["message"] == "OpenRouter API key cleared successfully"
        mock_settings_service.clear_openrouter_api_key.assert_called_once()

    def test_openrouter_api_key_endpoints_require_proper_http_methods(
        self, client, mock_settings_service
    ):
        """Test that endpoints only accept their designated HTTP methods."""
        # Test POST not allowed on GET/PUT/DELETE endpoint
        response = client.post("/api/v1/settings/openrouter-api-key")
        assert response.status_code == 405

        # Test PATCH not allowed
        response = client.patch("/api/v1/settings/openrouter-api-key")
        assert response.status_code == 405

    def test_settings_endpoint_includes_has_api_key_field(
        self, client, mock_settings_service
    ):
        """Test that main settings endpoint includes has_openrouter_api_key field."""
        # Setup
        settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
            openrouter_api_key_encrypted="encrypted_key_data",
        )

        mock_settings_service.get_settings.return_value = settings

        # Execute
        response = client.get("/api/v1/settings/")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "has_openrouter_api_key" in data["data"]
        assert data["data"]["has_openrouter_api_key"] is True

    def test_settings_endpoint_has_api_key_false_when_no_key(
        self, client, mock_settings_service
    ):
        """Test that settings endpoint shows false when no API key is set."""
        # Setup
        settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
            openrouter_api_key_encrypted=None,
        )

        mock_settings_service.get_settings.return_value = settings

        # Execute
        response = client.get("/api/v1/settings/")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "has_openrouter_api_key" in data["data"]
        assert data["data"]["has_openrouter_api_key"] is False
