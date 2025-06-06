"""Tests for the UserProfileService class."""

from unittest.mock import MagicMock

import pytest

from app.models.user_profile import UserProfile
from app.services.user_profile_service import UserProfileService
from app.utils.exceptions import (
    BusinessRuleError,
    ValidationError,
)


class TestUserProfileService:
    """Test the UserProfileService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock user profile repository."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a UserProfileService with a mock repository."""
        return UserProfileService(mock_repository)

    @pytest.fixture
    def sample_profile(self):
        """Create a sample user profile for testing."""
        return UserProfile(
            id=1,
            label="test_profile",
            name="Test User",
            avatar_image="test.png",
            description="A test user profile",
        )

    def test_get_profile(self, service, mock_repository, sample_profile):
        """Test getting a user profile by ID."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        # Execute
        result = service.get_profile(1)

        # Verify
        assert result == sample_profile
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_profile_by_label(self, service, mock_repository, sample_profile):
        """Test getting a user profile by label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_profile

        # Execute
        result = service.get_profile_by_label("test_profile")

        # Verify
        assert result == sample_profile
        mock_repository.get_by_label.assert_called_once_with("test_profile")

    def test_get_all_profiles(self, service, mock_repository, sample_profile):
        """Test getting all user profiles."""
        # Setup
        mock_repository.get_all.return_value = [sample_profile]

        # Execute
        result = service.get_all_profiles()

        # Verify
        assert result == [sample_profile]
        mock_repository.get_all.assert_called_once()

    def test_search_profiles(self, service, mock_repository, sample_profile):
        """Test searching for user profiles."""
        # Setup
        mock_repository.search.return_value = [sample_profile]

        # Execute
        result = service.search_profiles("test")

        # Verify
        assert result == [sample_profile]
        mock_repository.search.assert_called_once_with("test")

    def test_search_profiles_validation(self, service, mock_repository):
        """Test search validation for short queries."""
        with pytest.raises(ValidationError) as excinfo:
            service.search_profiles("")

        assert "Search query must be at least 2 characters" in str(excinfo.value)
        mock_repository.search.assert_not_called()

        with pytest.raises(ValidationError):
            service.search_profiles("a")
        mock_repository.search.assert_not_called()

    def test_get_profiles_by_name(self, service, mock_repository, sample_profile):
        """Test finding user profiles by name."""
        # Setup
        mock_repository.get_by_name.return_value = [sample_profile]

        # Execute
        result = service.get_profiles_by_name("Test")

        # Verify
        assert result == [sample_profile]
        mock_repository.get_by_name.assert_called_once_with("Test")

    def test_get_profiles_by_name_validation(self, service, mock_repository):
        """Test name search validation for short queries."""
        with pytest.raises(ValidationError) as excinfo:
            service.get_profiles_by_name("")

        assert "Name search query must be at least 2 characters" in str(excinfo.value)
        mock_repository.get_by_name.assert_not_called()

    def test_get_default_profile(self, service, mock_repository, sample_profile):
        """Test getting default user profile."""
        # Setup
        mock_repository.get_default_profile.return_value = sample_profile

        # Execute
        result = service.get_default_profile()

        # Verify
        assert result == sample_profile
        mock_repository.get_default_profile.assert_called_once()

    def test_create_profile(self, service, mock_repository):
        """Test creating a user profile."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing profile
        mock_repository.create.return_value = UserProfile(
            id=1, label="new_profile", name="New User"
        )

        # Execute
        result = service.create_profile(
            label="new_profile", name="New User", description="New description"
        )

        # Verify
        assert result.id == 1
        assert result.label == "new_profile"
        assert result.name == "New User"
        mock_repository.create.assert_called_once_with(
            label="new_profile",
            name="New User",
            avatar_image=None,
            description="New description",
        )

    def test_create_profile_label_exists(
        self, service, mock_repository, sample_profile
    ):
        """Test creating a user profile with existing label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_profile  # Existing profile

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_profile(
                label="test_profile", name="New User"  # Already exists
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.create.assert_not_called()

    def test_create_profile_validation_errors(self, service, mock_repository):
        """Test user profile creation validation."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing profile

        # Test empty label
        with pytest.raises(ValidationError) as excinfo:
            service.create_profile(label="", name="Test")

        assert "User profile validation failed" in str(excinfo.value)
        assert "required" in excinfo.value.details.get("label", "")

        # Test short label
        with pytest.raises(ValidationError) as excinfo:
            service.create_profile(label="a", name="Test")

        assert "User profile validation failed" in str(excinfo.value)
        assert "at least 2 characters" in excinfo.value.details.get("label", "")

        # Test empty name
        with pytest.raises(ValidationError) as excinfo:
            service.create_profile(label="test", name="")

        assert "User profile validation failed" in str(excinfo.value)
        assert "required" in excinfo.value.details.get("name", "")

        # Verify repository not called for any validation failures
        mock_repository.create.assert_not_called()

    def test_update_profile(self, service, mock_repository, sample_profile, mocker):
        """Test updating a user profile."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile
        mock_repository.get_by_label.return_value = None  # No conflict with new label

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.user_profile_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        updated_profile = UserProfile(
            id=1,
            label="updated_profile",
            name="Updated User",
            avatar_image="new.png",
            description="Updated description",
        )
        mock_repository.update.return_value = updated_profile

        # Execute
        result = service.update_profile(
            profile_id=1,
            label="updated_profile",
            name="Updated User",
            avatar_image="new.png",
            description="Updated description",
        )

        # Verify
        assert result == updated_profile
        mock_repository.update.assert_called_once_with(
            1,
            label="updated_profile",
            name="Updated User",
            avatar_image="new.png",
            description="Updated description",
        )
        # Should delete old avatar when updating to new one
        mock_file_service_instance.delete_avatar_image.assert_called_once_with(
            "test.png"
        )

    def test_update_profile_avatar_same(
        self, service, mock_repository, sample_profile, mocker
    ):
        """Test updating user profile with same avatar doesn't delete file."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile
        mock_repository.get_by_label.return_value = None

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.user_profile_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        updated_profile = UserProfile(
            id=1,
            label="updated_profile",
            name="Updated User",
            avatar_image="test.png",  # Same as original
            description="Updated description",
        )
        mock_repository.update.return_value = updated_profile

        # Execute
        result = service.update_profile(
            profile_id=1,
            label="updated_profile",
            name="Updated User",
            avatar_image="test.png",  # Same avatar
            description="Updated description",
        )

        # Verify - should not delete avatar file since it's the same
        assert result == updated_profile
        mock_file_service_instance.delete_avatar_image.assert_not_called()

    def test_update_profile_partial(self, service, mock_repository, sample_profile):
        """Test partially updating a user profile."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        updated_profile = UserProfile(
            id=1,
            label="test_profile",  # Unchanged
            name="Updated User",  # Only name is updated
            avatar_image="test.png",  # Unchanged
            description="A test user profile",  # Unchanged
        )
        mock_repository.update.return_value = updated_profile

        # Execute - only update name
        result = service.update_profile(profile_id=1, name="Updated User")

        # Verify
        assert result == updated_profile
        mock_repository.update.assert_called_once_with(1, name="Updated User")

    def test_update_profile_label_exists(
        self, service, mock_repository, sample_profile
    ):
        """Test updating a profile with a label that already exists on another profile."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        # Another profile with the label we want to use
        existing_profile = UserProfile(
            id=2, label="existing_label", name="Existing User"  # Different ID
        )
        mock_repository.get_by_label.return_value = existing_profile

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_profile(
                profile_id=1,
                label="existing_label",  # Already used by profile with ID 2
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.update.assert_not_called()

    def test_update_profile_same_label(self, service, mock_repository, sample_profile):
        """Test updating a profile with its own label is allowed."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile
        mock_repository.get_by_label.return_value = sample_profile  # Same profile

        updated_profile = UserProfile(
            id=1,
            label="test_profile",  # Same label
            name="Updated User",  # Only name is updated
            avatar_image="test.png",
            description="A test user profile",
        )
        mock_repository.update.return_value = updated_profile

        # Execute - update name but keep same label
        result = service.update_profile(
            profile_id=1, label="test_profile", name="Updated User"  # Same as current
        )

        # Verify - update should succeed since label belongs to same profile
        assert result == updated_profile
        mock_repository.update.assert_called_once_with(
            1, name="Updated User"  # Label not included in update since it's the same
        )

    def test_delete_profile(self, service, mock_repository, sample_profile, mocker):
        """Test deleting a user profile."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.user_profile_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        # Ensure default_in_settings is None
        sample_profile.default_in_settings = None

        # Execute
        service.delete_profile(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)
        mock_file_service_instance.delete_avatar_image.assert_called_once_with(
            "test.png"
        )

    def test_delete_profile_no_avatar(self, service, mock_repository, mocker):
        """Test deleting a user profile without avatar doesn't try to delete file."""
        # Setup - profile without avatar
        profile_no_avatar = UserProfile(
            id=1,
            label="test_profile",
            name="Test User",
            avatar_image=None,
            description="A test user profile",
        )
        mock_repository.get_by_id.return_value = profile_no_avatar

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock FileUploadService
        mock_file_service = mocker.patch(
            "app.services.user_profile_service.FileUploadService"
        )
        mock_file_service_instance = mock_file_service.return_value

        # Ensure default_in_settings is None
        profile_no_avatar.default_in_settings = None

        # Execute
        service.delete_profile(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)
        mock_file_service_instance.delete_avatar_image.assert_not_called()

    def test_delete_profile_with_sessions(
        self, service, mock_repository, sample_profile, mocker
    ):
        """Test cannot delete profile that is used in chat sessions."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        # Mock chat_sessions relationship with non-zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=2)

        # Ensure default_in_settings is None
        sample_profile.default_in_settings = None

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_profile(1)

        assert "Cannot delete user profile that is used in chat sessions" in str(
            excinfo.value
        )
        mock_repository.delete.assert_not_called()

    def test_delete_profile_used_as_default(
        self, service, mock_repository, sample_profile, mocker
    ):
        """Test cannot delete profile that is set as default in settings."""
        # Setup
        mock_repository.get_by_id.return_value = sample_profile

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock default_in_settings as non-None
        sample_profile.default_in_settings = MagicMock()

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_profile(1)

        assert (
            "Cannot delete user profile that is set as default in application settings"
            in str(excinfo.value)
        )
        mock_repository.delete.assert_not_called()
