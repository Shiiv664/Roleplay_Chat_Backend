"""Tests for the Characters API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.character import Character
from app.utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def mock_character_service():
    """Create a mock for the CharacterService."""
    with patch("app.api.namespaces.characters.CharacterService") as mock_service_class:
        # Create a mock service instance
        mock_service = MagicMock()
        # Configure the class to return our mock when instantiated
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "id": 1,
        "label": "test_character",
        "name": "Test Character",
        "description": "A test character description",
        "avatar_image": None,
        "created_at": "2023-05-18T12:00:00",
        "updated_at": "2023-05-18T12:00:00",
    }


@pytest.fixture
def sample_character(sample_character_data):
    """Create a sample character object from sample data."""
    character = Character(
        id=sample_character_data["id"],
        label=sample_character_data["label"],
        name=sample_character_data["name"],
        description=sample_character_data["description"],
        avatar_image=sample_character_data["avatar_image"],
    )
    return character


class TestCharactersAPI:
    """Test the Characters API endpoints."""

    def test_get_characters_list(
        self, client, mock_character_service, sample_character
    ):
        """Test getting a list of characters."""
        # Configure the mock
        mock_character_service.get_all_characters.return_value = [sample_character]

        # Execute API request
        response = client.get("/api/v1/characters/")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_character.id
        assert data["data"][0]["label"] == sample_character.label
        assert data["data"][0]["name"] == sample_character.name

        # Verify service was called
        mock_character_service.get_all_characters.assert_called_once()

    def test_get_character_by_id(
        self, client, mock_character_service, sample_character
    ):
        """Test getting a character by ID."""
        # Configure the mock
        mock_character_service.get_character.return_value = sample_character

        # Execute API request
        response = client.get(f"/api/v1/characters/{sample_character.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_character.id
        assert data["data"]["label"] == sample_character.label
        assert data["data"]["name"] == sample_character.name

        # Verify service was called with correct ID
        mock_character_service.get_character.assert_called_once_with(
            sample_character.id
        )

    def test_get_character_not_found(self, client, mock_character_service):
        """Test getting a non-existent character."""
        # Configure the mock to raise an exception
        mock_character_service.get_character.side_effect = ResourceNotFoundError(
            "Character with ID 999 not found"
        )

        # Execute API request
        response = client.get("/api/v1/characters/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "not found" in data["error"]["message"]

        # Verify service was called
        mock_character_service.get_character.assert_called_once_with(999)

    def test_create_character(self, client, mock_character_service, sample_character):
        """Test creating a new character."""
        # Data to send in request
        character_data = {
            "label": "new_character",
            "name": "New Character",
            "description": "A new character for testing",
        }

        # Configure the mock
        mock_character_service.create_character.return_value = sample_character

        # Execute API request
        response = client.post(
            "/api/v1/characters/",
            data=json.dumps(character_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_character.id

        # Verify service was called with correct arguments
        mock_character_service.create_character.assert_called_once_with(
            label="new_character",
            name="New Character",
            description="A new character for testing",
            avatar_image=None,
            first_messages=None,
        )

    def test_create_character_validation_error(self, client, mock_character_service):
        """Test validation error when creating a character."""
        # Missing required 'name' field
        character_data = {
            "label": "invalid_character",
            "description": "This should fail validation",
        }

        # Configure the mock to raise validation error
        error_details = {"name": "Character name is required"}
        mock_character_service.create_character.side_effect = ValidationError(
            "Character validation failed", details=error_details
        )

        # Execute API request
        response = client.post(
            "/api/v1/characters/",
            data=json.dumps(character_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["name"] == "Character name is required"

    def test_update_character(self, client, mock_character_service, sample_character):
        """Test updating a character."""
        # Data to send in update request
        update_data = {
            "name": "Updated Character",
            "description": "Updated description",
        }

        # Create an updated character based on the sample
        updated_character = Character(
            id=sample_character.id,
            label=sample_character.label,
            name="Updated Character",
            description="Updated description",
            avatar_image=sample_character.avatar_image,
        )

        # Configure the mock
        mock_character_service.update_character.return_value = updated_character

        # Execute API request
        response = client.put(
            f"/api/v1/characters/{sample_character.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_character.id
        assert data["data"]["name"] == "Updated Character"
        assert data["data"]["description"] == "Updated description"

        # Verify service was called with correct arguments
        mock_character_service.update_character.assert_called_once_with(
            character_id=sample_character.id,
            label=None,
            name="Updated Character",
            description="Updated description",
            avatar_image=None,
            first_messages=None,
        )

    def test_update_character_not_found(self, client, mock_character_service):
        """Test updating a non-existent character."""
        # Data to send in update request
        update_data = {
            "name": "Updated Character",
            "description": "Updated description",
        }

        # Configure the mock to raise an exception
        mock_character_service.update_character.side_effect = ResourceNotFoundError(
            "Character with ID 999 not found"
        )

        # Execute API request
        response = client.put(
            "/api/v1/characters/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_character(self, client, mock_character_service, sample_character):
        """Test deleting a character."""
        # Configure the mock
        # Note: delete_character does not return anything, so we don't need to configure a return value

        # Execute API request
        response = client.delete(f"/api/v1/characters/{sample_character.id}")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["id"] == sample_character.id
        assert "deleted" in data["data"]["message"].lower()

        # Verify service was called with correct ID and chat session service
        call_args = mock_character_service.delete_character.call_args
        assert call_args[0][0] == sample_character.id  # First argument is character ID
        assert call_args[0][1] is not None  # Second argument is chat session service
        mock_character_service.delete_character.assert_called_once()

    def test_delete_character_not_found(self, client, mock_character_service):
        """Test deleting a non-existent character."""
        # Configure the mock to raise an exception
        mock_character_service.delete_character.side_effect = ResourceNotFoundError(
            "Character with ID 999 not found"
        )

        # Execute API request
        response = client.delete("/api/v1/characters/999")

        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_search_characters(self, client, mock_character_service, sample_character):
        """Test searching for characters."""
        # Configure the mock
        mock_character_service.search_characters.return_value = [sample_character]

        # Execute API request
        response = client.get("/api/v1/characters/search?query=test")

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_character.id
        assert data["data"][0]["label"] == sample_character.label
        assert data["meta"]["query"] == "test"

        # Verify service was called with correct arguments
        mock_character_service.search_characters.assert_called_once_with("test")

    def test_search_characters_validation_error(self, client, mock_character_service):
        """Test validation error when searching with a short query."""
        # Configure the mock to raise validation error
        mock_character_service.search_characters.side_effect = ValidationError(
            "Search query must be at least 2 characters"
        )

        # Execute API request with a single character query
        response = client.get("/api/v1/characters/search?query=a")

        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
