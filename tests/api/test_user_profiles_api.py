"""Tests for the User Profiles API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.user_profile import UserProfile
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_user_profile_service():
    """Create a mock for the UserProfileService."""
    with patch(
        "app.api.namespaces.user_profiles.UserProfileService"
    ) as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_user_profile_data():
    """Sample user profile data for testing."""
    return {
        "id": 1,
        "label": "test_profile",
        "name": "Test User",
        "description": "A test user profile description",
        "avatar_image": "test_avatar.jpg",
        "created_at": "2023-05-18T12:00:00",
        "updated_at": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_user_profile(sample_user_profile_data):
    """Create a sample user profile object from sample data."""
    profile = UserProfile(
        id=sample_user_profile_data["id"],
        label=sample_user_profile_data["label"],
        name=sample_user_profile_data["name"],
        description=sample_user_profile_data["description"],
        avatar_image=sample_user_profile_data["avatar_image"],
    )
    return profile


class TestUserProfilesAPI:
    """Test the User Profiles API endpoints."""

    def test_get_user_profiles_list(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test getting a list of user profiles."""
        # Configure the mock
        mock_user_profile_service.get_all_profiles.return_value = [sample_user_profile]

        # Execute API request
        response = client.get("/api/v1/user-profiles/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_user_profile.id
        assert data["data"][0]["label"] == sample_user_profile.label
        assert data["data"][0]["name"] == sample_user_profile.name

        # Verify service was called
        mock_user_profile_service.get_all_profiles.assert_called_once()

    def test_get_user_profile_by_id(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test getting a user profile by ID."""
        # Configure the mock
        mock_user_profile_service.get_profile.return_value = sample_user_profile

        # Execute API request
        response = client.get(f"/api/v1/user-profiles/{sample_user_profile.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_user_profile.id
        assert data["data"]["label"] == sample_user_profile.label
        assert data["data"]["name"] == sample_user_profile.name

        # Verify service was called with correct ID
        mock_user_profile_service.get_profile.assert_called_once_with(
            sample_user_profile.id
        )

    def test_get_user_profile_not_found(self, client, mock_user_profile_service):
        """Test getting a non-existent user profile."""
        # Configure the mock to raise an exception
        mock_user_profile_service.get_profile.side_effect = ResourceNotFoundError(
            "User profile with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/user-profiles/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_user_profile_service.get_profile.assert_called_once_with(999)

    def test_create_user_profile(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test creating a new user profile."""
        # Data to send in request
        profile_data = {
            "label": "new_profile",
            "name": "New User",
            "description": "A new user profile for testing",
            "avatar_image": "new_avatar.jpg",
        }

        # Configure the mock
        mock_user_profile_service.create_profile.return_value = sample_user_profile

        # Execute API request
        response = client.post(
            "/api/v1/user-profiles/",
            data=json.dumps(profile_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_user_profile.id

        # Verify service was called with correct arguments
        mock_user_profile_service.create_profile.assert_called_once_with(
            label="new_profile",
            name="New User",
            description="A new user profile for testing",
            avatar_image="new_avatar.jpg",
        )

    def test_create_user_profile_validation_error(
        self, client, mock_user_profile_service
    ):
        """Test validation error when creating a user profile."""
        # Missing required 'name' field
        profile_data = {
            "label": "invalid_profile",
            "description": "This should fail validation",
        }

        # Configure the mock to raise validation error
        error_details = {"name": "User profile name is required"}
        mock_user_profile_service.create_profile.side_effect = ValidationError(
            "User profile validation failed", details=error_details
        )

        # Execute API request
        response = client.post(
            "/api/v1/user-profiles/",
            data=json.dumps(profile_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["name"] == "User profile name is required"

    def test_update_user_profile(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test updating a user profile."""
        # Data to send in update request
        update_data = {"name": "Updated User", "description": "Updated description"}

        # Create an updated profile based on the sample
        updated_profile = UserProfile(
            id=sample_user_profile.id,
            label=sample_user_profile.label,
            name="Updated User",
            description="Updated description",
            avatar_image=sample_user_profile.avatar_image,
        )

        # Configure the mock
        mock_user_profile_service.update_profile.return_value = updated_profile

        # Execute API request
        response = client.put(
            f"/api/v1/user-profiles/{sample_user_profile.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_user_profile.id
        assert data["data"]["name"] == "Updated User"
        assert data["data"]["description"] == "Updated description"

        # Verify service was called with correct arguments
        mock_user_profile_service.update_profile.assert_called_once_with(
            profile_id=sample_user_profile.id,
            name="Updated User",
            description="Updated description",
            label=None,
            avatar_image=None,
        )

    def test_update_user_profile_not_found(self, client, mock_user_profile_service):
        """Test updating a non-existent user profile."""
        # Data to send in update request
        update_data = {"name": "Updated User", "description": "Updated description"}

        # Configure the mock to raise an exception
        mock_user_profile_service.update_profile.side_effect = ResourceNotFoundError(
            "User profile with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/user-profiles/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_user_profile(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test deleting a user profile."""
        # Configure the mock
        # Note: delete_profile does not return anything, so we don't need to configure a return value

        # Execute API request
        response = client.delete(f"/api/v1/user-profiles/{sample_user_profile.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_user_profile.id
        assert "deleted" in data["data"]["message"].lower()

        # Verify service was called with correct ID
        mock_user_profile_service.delete_profile.assert_called_once_with(
            sample_user_profile.id
        )

    def test_delete_user_profile_not_found(self, client, mock_user_profile_service):
        """Test deleting a non-existent user profile."""
        # Configure the mock to raise an exception
        mock_user_profile_service.delete_profile.side_effect = ResourceNotFoundError(
            "User profile with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/user-profiles/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_search_user_profiles(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test searching for user profiles."""
        # Configure the mock
        mock_user_profile_service.search_profiles.return_value = [sample_user_profile]

        # Execute API request
        response = client.get("/api/v1/user-profiles/search?query=test")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_user_profile.id
        assert data["data"][0]["label"] == sample_user_profile.label
        assert data["meta"]["query"] == "test"

        # Verify service was called with correct arguments
        mock_user_profile_service.search_profiles.assert_called_once_with("test")

    def test_search_user_profiles_validation_error(
        self, client, mock_user_profile_service
    ):
        """Test validation error when searching with a short query."""
        # Configure the mock to raise validation error
        mock_user_profile_service.search_profiles.side_effect = ValidationError(
            "Search query must be at least 2 characters"
        )

        # Execute API request with a single character query
        response = client.get("/api/v1/user-profiles/search?query=a")

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_default_user_profile(
        self, client, mock_user_profile_service, sample_user_profile
    ):
        """Test getting the default user profile."""
        # Configure the mock
        mock_user_profile_service.get_default_profile.return_value = sample_user_profile

        # Execute API request
        response = client.get("/api/v1/user-profiles/default")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_user_profile.id
        assert data["data"]["label"] == sample_user_profile.label

        # Verify service was called
        mock_user_profile_service.get_default_profile.assert_called_once()

    def test_get_default_user_profile_not_found(
        self, client, mock_user_profile_service
    ):
        """Test when no default user profile is set."""
        # Configure the mock to return None (no default profile)
        mock_user_profile_service.get_default_profile.return_value = None

        # Execute API request
        response = client.get("/api/v1/user-profiles/default")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "no default user profile" in data["error"]["message"].lower()

        # Verify service was called
        mock_user_profile_service.get_default_profile.assert_called_once()
