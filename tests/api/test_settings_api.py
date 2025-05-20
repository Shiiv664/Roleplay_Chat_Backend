"""Tests for the Application Settings API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.ai_model import AIModel
from app.models.application_settings import ApplicationSettings
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_application_settings_service():
    """Create a mock for the ApplicationSettingsService."""
    with patch(
        "app.api.namespaces.settings.ApplicationSettingsService"
    ) as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_ai_model():
    """Create a sample AI model for testing."""
    return AIModel(
        id=1, label="gpt-3.5-turbo", description="OpenAI's GPT-3.5 Turbo model"
    )


@pytest.fixture
def sample_system_prompt():
    """Create a sample system prompt for testing."""
    return SystemPrompt(
        id=1,
        label="basic_roleplay",
        content="You are roleplaying as the character described. Stay in character at all times.",
    )


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        id=1, label="default_user", name="Default User", avatar_image="default_user.jpg"
    )


@pytest.fixture
def sample_application_settings(
    sample_ai_model, sample_system_prompt, sample_user_profile
):
    """Create a sample application settings object for testing."""
    settings = ApplicationSettings(
        id=1,
        default_ai_model_id=sample_ai_model.id,
        default_system_prompt_id=sample_system_prompt.id,
        default_user_profile_id=sample_user_profile.id,
        default_avatar_image="default_avatar.jpg",
    )

    # Set up relationships for testing
    settings.default_ai_model = sample_ai_model
    settings.default_system_prompt = sample_system_prompt
    settings.default_user_profile = sample_user_profile

    return settings


class TestApplicationSettingsAPI:
    """Test the Application Settings API endpoints."""

    def test_get_settings(
        self, client, mock_application_settings_service, sample_application_settings
    ):
        """Test getting application settings."""
        # Configure the mock
        mock_application_settings_service.get_settings.return_value = (
            sample_application_settings
        )

        # Execute API request
        response = client.get("/api/v1/settings/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert (
            data["data"]["default_ai_model_id"]
            == sample_application_settings.default_ai_model_id
        )
        assert (
            data["data"]["default_system_prompt_id"]
            == sample_application_settings.default_system_prompt_id
        )
        assert (
            data["data"]["default_user_profile_id"]
            == sample_application_settings.default_user_profile_id
        )
        assert (
            data["data"]["default_avatar_image"]
            == sample_application_settings.default_avatar_image
        )

        # Check for related entities
        assert (
            data["data"]["default_ai_model"]["id"]
            == sample_application_settings.default_ai_model.id
        )
        assert (
            data["data"]["default_system_prompt"]["id"]
            == sample_application_settings.default_system_prompt.id
        )
        assert (
            data["data"]["default_user_profile"]["id"]
            == sample_application_settings.default_user_profile.id
        )

        # Verify service was called
        mock_application_settings_service.get_settings.assert_called_once()

    def test_update_settings_full(
        self, client, mock_application_settings_service, sample_application_settings
    ):
        """Test updating all application settings."""
        # Create updated settings
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=2,
            default_system_prompt_id=3,
            default_user_profile_id=4,
            default_avatar_image="new_avatar.jpg",
        )

        # Set up updated related entities
        updated_settings.default_ai_model = AIModel(
            id=2, label="gpt-4", description="OpenAI's GPT-4 model"
        )
        updated_settings.default_system_prompt = SystemPrompt(
            id=3, label="creative_writing", content="Write in a creative style..."
        )
        updated_settings.default_user_profile = UserProfile(
            id=4,
            label="premium_user",
            name="Premium User",
            avatar_image="premium_user.jpg",
        )

        # Configure the mock
        mock_application_settings_service.update_settings.return_value = (
            updated_settings
        )

        # Data to send in request
        update_data = {
            "default_ai_model_id": 2,
            "default_system_prompt_id": 3,
            "default_user_profile_id": 4,
            "default_avatar_image": "new_avatar.jpg",
        }

        # Execute API request
        response = client.put(
            "/api/v1/settings/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["default_ai_model_id"] == 2
        assert data["data"]["default_system_prompt_id"] == 3
        assert data["data"]["default_user_profile_id"] == 4
        assert data["data"]["default_avatar_image"] == "new_avatar.jpg"

        # Verify service was called with correct arguments
        mock_application_settings_service.update_settings.assert_called_once_with(
            default_ai_model_id=2,
            default_system_prompt_id=3,
            default_user_profile_id=4,
            default_avatar_image="new_avatar.jpg",
        )

    def test_update_settings_partial(
        self, client, mock_application_settings_service, sample_application_settings
    ):
        """Test updating only some application settings."""
        # Create partially updated settings
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=2,
            default_system_prompt_id=sample_application_settings.default_system_prompt_id,
            default_user_profile_id=sample_application_settings.default_user_profile_id,
            default_avatar_image="new_avatar.jpg",
        )

        # Set up relationships (only updated ones)
        updated_settings.default_ai_model = AIModel(
            id=2, label="gpt-4", description="OpenAI's GPT-4 model"
        )
        updated_settings.default_system_prompt = (
            sample_application_settings.default_system_prompt
        )
        updated_settings.default_user_profile = (
            sample_application_settings.default_user_profile
        )

        # Configure the mock
        mock_application_settings_service.update_settings.return_value = (
            updated_settings
        )

        # Data to send in request (only two fields)
        update_data = {
            "default_ai_model_id": 2,
            "default_avatar_image": "new_avatar.jpg",
        }

        # Execute API request
        response = client.put(
            "/api/v1/settings/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["default_ai_model_id"] == 2
        assert (
            data["data"]["default_system_prompt_id"]
            == sample_application_settings.default_system_prompt_id
        )
        assert (
            data["data"]["default_user_profile_id"]
            == sample_application_settings.default_user_profile_id
        )
        assert data["data"]["default_avatar_image"] == "new_avatar.jpg"

        # Verify service was called with correct arguments (only the fields that were provided)
        mock_application_settings_service.update_settings.assert_called_once_with(
            default_ai_model_id=2, default_avatar_image="new_avatar.jpg"
        )

    def test_update_settings_validation_error(
        self, client, mock_application_settings_service
    ):
        """Test validation error when updating application settings."""
        # Configure the mock to raise validation error
        mock_application_settings_service.update_settings.side_effect = ValidationError(
            "Avatar path cannot be empty string",
            details={
                "default_avatar_image": "Must provide a valid path or URL, or None"
            },
        )

        # Data with empty avatar path
        update_data = {"default_avatar_image": ""}

        # Execute API request
        response = client.put(
            "/api/v1/settings/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert (
            data["error"]["details"]["default_avatar_image"]
            == "Must provide a valid path or URL, or None"
        )

    def test_update_settings_resource_not_found(
        self, client, mock_application_settings_service
    ):
        """Test resource not found error when updating application settings."""
        # Configure the mock to raise resource not found error
        mock_application_settings_service.update_settings.side_effect = (
            ResourceNotFoundError("AI Model with ID 999 not found")
        )

        # Data with non-existent AI model ID
        update_data = {"default_ai_model_id": 999}

        # Execute API request
        response = client.put(
            "/api/v1/settings/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_reset_settings(self, client, mock_application_settings_service):
        """Test resetting application settings."""
        # Create reset settings with null values
        reset_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
        )

        # Configure the mock
        mock_application_settings_service.reset_settings.return_value = reset_settings

        # Execute API request
        response = client.post("/api/v1/settings/reset")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["message"] == "Application settings reset to defaults"
        assert data["data"]["settings"]["id"] == 1
        assert data["data"]["settings"]["default_ai_model_id"] is None
        assert data["data"]["settings"]["default_system_prompt_id"] is None
        assert data["data"]["settings"]["default_user_profile_id"] is None
        assert data["data"]["settings"]["default_avatar_image"] is None

        # Verify service was called
        mock_application_settings_service.reset_settings.assert_called_once()
