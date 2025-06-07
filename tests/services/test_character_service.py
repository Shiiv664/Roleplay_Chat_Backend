"""Tests for the CharacterService class."""

from unittest.mock import MagicMock

import pytest

from app.models.character import Character
from app.services.character_service import CharacterService
from app.utils.exceptions import ValidationError


class TestCharacterService:
    """Test the CharacterService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock character repository."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a CharacterService with a mock repository."""
        return CharacterService(mock_repository)

    @pytest.fixture
    def sample_character(self):
        """Create a sample character for testing."""
        return Character(
            id=1,
            label="test_char",
            name="Test Character",
            avatar_image="test.png",
            description="A test character",
        )

    def test_get_character(self, service, mock_repository, sample_character):
        """Test getting a character by ID."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        # Execute
        result = service.get_character(1)

        # Verify
        assert result == sample_character
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_character_by_label(self, service, mock_repository, sample_character):
        """Test getting a character by label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_character

        # Execute
        result = service.get_character_by_label("test_char")

        # Verify
        assert result == sample_character
        mock_repository.get_by_label.assert_called_once_with("test_char")

    def test_get_all_characters(self, service, mock_repository, sample_character):
        """Test getting all characters."""
        # Setup
        mock_repository.get_all.return_value = [sample_character]

        # Execute
        result = service.get_all_characters()

        # Verify
        assert result == [sample_character]
        mock_repository.get_all.assert_called_once()

    def test_search_characters(self, service, mock_repository, sample_character):
        """Test searching for characters."""
        # Setup
        mock_repository.search.return_value = [sample_character]

        # Execute
        result = service.search_characters("test")

        # Verify
        assert result == [sample_character]
        mock_repository.search.assert_called_once_with("test")

    def test_search_characters_validation(self, service):
        """Test search validation for short queries."""
        with pytest.raises(ValidationError):
            service.search_characters("")

        with pytest.raises(ValidationError):
            service.search_characters("a")

    def test_create_character(self, service, mock_repository):
        """Test creating a character."""
        # Setup
        mock_repository.get_by_label.return_value = None
        mock_repository.create.return_value = Character(
            id=1, label="new_char", name="New Character"
        )

        # Execute
        result = service.create_character(
            label="new_char", name="New Character", description="New description"
        )

        # Verify
        assert result.id == 1
        assert result.label == "new_char"
        assert result.name == "New Character"
        mock_repository.create.assert_called_once_with(
            label="new_char",
            name="New Character",
            avatar_image=None,
            description="New description",
            first_messages=None,
        )

    def test_create_character_label_exists(
        self, service, mock_repository, sample_character
    ):
        """Test creating a character with existing label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_character

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_character(
                label="test_char", name="New Character"  # Already exists
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.create.assert_not_called()

    def test_create_character_validation_errors(self, service, mock_repository):
        """Test character creation validation."""
        # Setup
        mock_repository.get_by_label.return_value = None

        # Test empty label
        with pytest.raises(ValidationError) as excinfo:
            service.create_character(label="", name="Test")

        assert "Character validation failed" in str(excinfo.value)
        assert "required" in str(excinfo.value.details.get("label", ""))

        # Test short label
        with pytest.raises(ValidationError) as excinfo:
            service.create_character(label="a", name="Test")

        assert "Character validation failed" in str(excinfo.value)
        assert "at least 2 characters" in str(excinfo.value.details.get("label", ""))

        # Test empty name
        with pytest.raises(ValidationError) as excinfo:
            service.create_character(label="test", name="")

        assert "Character validation failed" in str(excinfo.value)
        assert "required" in str(excinfo.value.details.get("name", ""))

        # Verify repository not called for any validation failures
        mock_repository.create.assert_not_called()

    def test_update_character(self, service, mock_repository, sample_character, mocker):
        """Test updating a character."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character
        mock_repository.get_by_label.return_value = None  # No conflict with new label

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.character_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        updated_character = Character(
            id=1,
            label="updated_char",
            name="Updated Character",
            avatar_image="new.png",
            description="Updated description",
        )
        mock_repository.update.return_value = updated_character

        # Execute
        result = service.update_character(
            character_id=1,
            label="updated_char",
            name="Updated Character",
            avatar_image="new.png",
            description="Updated description",
        )

        # Verify
        assert result == updated_character
        mock_repository.update.assert_called_once_with(
            1,
            label="updated_char",
            name="Updated Character",
            avatar_image="new.png",
            description="Updated description",
        )
        # Should delete old avatar when updating to new one
        mock_file_service_instance.delete_avatar_image.assert_called_once_with(
            "test.png"
        )

    def test_update_character_avatar_same(
        self, service, mock_repository, sample_character, mocker
    ):
        """Test updating character with same avatar doesn't delete file."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character
        mock_repository.get_by_label.return_value = None

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.character_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        updated_character = Character(
            id=1,
            label="updated_char",
            name="Updated Character",
            avatar_image="test.png",  # Same as original
            description="Updated description",
        )
        mock_repository.update.return_value = updated_character

        # Execute
        result = service.update_character(
            character_id=1,
            label="updated_char",
            name="Updated Character",
            avatar_image="test.png",  # Same avatar
            description="Updated description",
        )

        # Verify - should not delete avatar file since it's the same
        assert result == updated_character
        mock_file_service_instance.delete_avatar_image.assert_not_called()

    def test_update_character_partial(self, service, mock_repository, sample_character):
        """Test partially updating a character."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        updated_character = Character(
            id=1,
            label="test_char",  # Unchanged
            name="Updated Character",  # Only name is updated
            avatar_image="test.png",  # Unchanged
            description="A test character",  # Unchanged
        )
        mock_repository.update.return_value = updated_character

        # Execute - only update name
        result = service.update_character(character_id=1, name="Updated Character")

        # Verify
        assert result == updated_character
        mock_repository.update.assert_called_once_with(1, name="Updated Character")

    def test_update_character_label_exists(
        self, service, mock_repository, sample_character
    ):
        """Test updating a character with a label that already exists on another character."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        # Another character with the label we want to use
        existing_character = Character(
            id=2, label="existing_label", name="Existing Character"  # Different ID
        )
        mock_repository.get_by_label.return_value = existing_character

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_character(
                character_id=1,
                label="existing_label",  # Already used by character with ID 2
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.update.assert_not_called()

    def test_update_character_same_label(
        self, service, mock_repository, sample_character
    ):
        """Test updating a character with its own label is allowed."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character
        mock_repository.get_by_label.return_value = sample_character  # Same character

        updated_character = Character(
            id=1,
            label="test_char",  # Same label
            name="Updated Character",  # Only name is updated
            avatar_image="test.png",
            description="A test character",
        )
        mock_repository.update.return_value = updated_character

        # Execute - update name but keep same label
        result = service.update_character(
            character_id=1,
            label="test_char",  # Same as current
            name="Updated Character",
        )

        # Verify - update should succeed since label belongs to same character
        assert result == updated_character
        mock_repository.update.assert_called_once_with(
            1,
            name="Updated Character",  # Label not included in update since it's the same
        )

    def test_delete_character(self, service, mock_repository, sample_character, mocker):
        """Test deleting a character."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        # Patch the count method to return zero
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.character_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        # Execute
        service.delete_character(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)
        mock_file_service_instance.delete_avatar_image.assert_called_once_with(
            "test.png"
        )

    def test_delete_character_no_avatar(self, service, mock_repository, mocker):
        """Test deleting a character without avatar doesn't try to delete file."""
        # Setup - character without avatar
        character_no_avatar = Character(
            id=1,
            label="test_char",
            name="Test Character",
            avatar_image=None,
            description="A test character",
        )
        mock_repository.get_by_id.return_value = character_no_avatar

        # Patch the count method to return zero
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.character_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        # Execute
        service.delete_character(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)
        mock_file_service_instance.delete_avatar_image.assert_not_called()

    def test_delete_character_without_chat_session_service(
        self, service, mock_repository, sample_character, mocker
    ):
        """Test deleting character without chat session service (backward compatibility)."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        # Mock file service
        mocker.patch("app.services.character_service.FileUploadService")

        # Execute - should work even without chat session service (old behavior)
        service.delete_character(1)

        # Verify character was deleted
        mock_repository.delete.assert_called_once_with(1)

    def test_delete_character_with_chat_session_service(
        self, service, mock_repository, sample_character, mocker
    ):
        """Test deleting character with chat session service deletes related sessions."""
        # Setup
        mock_repository.get_by_id.return_value = sample_character

        # Mock chat session service
        mock_chat_service = mocker.MagicMock()
        mock_sessions = [mocker.MagicMock(id=1), mocker.MagicMock(id=2)]
        mock_chat_service.get_sessions_by_character.return_value = mock_sessions

        # Mock file service
        mocker.patch("app.services.character_service.FileUploadService")

        # Execute
        service.delete_character(1, mock_chat_service)

        # Verify chat sessions were retrieved and deleted
        mock_chat_service.get_sessions_by_character.assert_called_once_with(1)
        assert mock_chat_service.delete_session.call_count == 2
        mock_chat_service.delete_session.assert_any_call(1)
        mock_chat_service.delete_session.assert_any_call(2)

        # Verify character was deleted
        mock_repository.delete.assert_called_once_with(1)
