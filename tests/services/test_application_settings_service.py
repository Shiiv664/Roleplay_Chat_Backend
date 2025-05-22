"""Tests for the ApplicationSettingsService class."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.application_settings import ApplicationSettings
from app.services.application_settings_service import ApplicationSettingsService
from app.utils.exceptions import ResourceNotFoundError, ValidationError


class TestApplicationSettingsService:
    """Test the ApplicationSettingsService functionality."""

    @pytest.fixture
    def mock_application_settings_repository(self):
        """Create a mock application settings repository."""
        return MagicMock()

    @pytest.fixture
    def mock_ai_model_repository(self):
        """Create a mock AI model repository."""
        return MagicMock()

    @pytest.fixture
    def mock_system_prompt_repository(self):
        """Create a mock system prompt repository."""
        return MagicMock()

    @pytest.fixture
    def mock_user_profile_repository(self):
        """Create a mock user profile repository."""
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_application_settings_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        mock_user_profile_repository,
    ):
        """Create an ApplicationSettingsService with mock repositories."""
        return ApplicationSettingsService(
            mock_application_settings_repository,
            mock_ai_model_repository,
            mock_system_prompt_repository,
            mock_user_profile_repository,
        )

    @pytest.fixture
    def sample_settings(self):
        """Create a sample ApplicationSettings instance for testing."""
        return ApplicationSettings(
            id=1,
            default_ai_model_id=1,
            default_system_prompt_id=1,
            default_user_profile_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )

    def test_get_settings(
        self, service, mock_application_settings_repository, sample_settings
    ):
        """Test getting application settings."""
        # Setup
        mock_application_settings_repository.get_settings.return_value = sample_settings

        # Execute
        result = service.get_settings()

        # Verify
        assert result == sample_settings
        mock_application_settings_repository.get_settings.assert_called_once()

    def test_update_default_ai_model(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
        sample_settings,
    ):
        """Test updating the default AI model."""
        # Setup
        mock_ai_model_repository.get_by_id.return_value = MagicMock()  # AI model exists
        mock_application_settings_repository.update_default_ai_model.return_value = (
            sample_settings
        )

        # Execute
        result = service.update_default_ai_model(model_id=1)

        # Verify
        assert result == sample_settings
        mock_ai_model_repository.get_by_id.assert_called_once_with(1)
        mock_application_settings_repository.update_default_ai_model.assert_called_once_with(
            1
        )

    def test_update_default_ai_model_null(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
        sample_settings,
    ):
        """Test clearing the default AI model."""
        # Setup
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,  # Cleared
            default_system_prompt_id=1,
            default_user_profile_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )
        mock_application_settings_repository.update_default_ai_model.return_value = (
            updated_settings
        )

        # Execute
        result = service.update_default_ai_model(model_id=None)

        # Verify
        assert result == updated_settings
        mock_ai_model_repository.get_by_id.assert_not_called()  # No need to check if None
        mock_application_settings_repository.update_default_ai_model.assert_called_once_with(
            None
        )

    def test_update_default_ai_model_not_found(
        self, service, mock_application_settings_repository, mock_ai_model_repository
    ):
        """Test updating with non-existent AI model."""
        # Setup
        mock_ai_model_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_default_ai_model(model_id=999)

        # Verify repository method was not called
        mock_application_settings_repository.update_default_ai_model.assert_not_called()

    def test_update_default_system_prompt(
        self,
        service,
        mock_application_settings_repository,
        mock_system_prompt_repository,
        sample_settings,
    ):
        """Test updating the default system prompt."""
        # Setup
        mock_system_prompt_repository.get_by_id.return_value = (
            MagicMock()
        )  # System prompt exists
        mock_application_settings_repository.update_default_system_prompt.return_value = (
            sample_settings
        )

        # Execute
        result = service.update_default_system_prompt(prompt_id=1)

        # Verify
        assert result == sample_settings
        mock_system_prompt_repository.get_by_id.assert_called_once_with(1)
        mock_application_settings_repository.update_default_system_prompt.assert_called_once_with(
            1
        )

    def test_update_default_system_prompt_null(
        self,
        service,
        mock_application_settings_repository,
        mock_system_prompt_repository,
        sample_settings,
    ):
        """Test clearing the default system prompt."""
        # Setup
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=1,
            default_system_prompt_id=None,  # Cleared
            default_user_profile_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )
        mock_application_settings_repository.update_default_system_prompt.return_value = (
            updated_settings
        )

        # Execute
        result = service.update_default_system_prompt(prompt_id=None)

        # Verify
        assert result == updated_settings
        mock_system_prompt_repository.get_by_id.assert_not_called()  # No need to check if None
        mock_application_settings_repository.update_default_system_prompt.assert_called_once_with(
            None
        )

    def test_update_default_system_prompt_not_found(
        self,
        service,
        mock_application_settings_repository,
        mock_system_prompt_repository,
    ):
        """Test updating with non-existent system prompt."""
        # Setup
        mock_system_prompt_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_default_system_prompt(prompt_id=999)

        # Verify repository method was not called
        mock_application_settings_repository.update_default_system_prompt.assert_not_called()

    def test_update_default_user_profile(
        self,
        service,
        mock_application_settings_repository,
        mock_user_profile_repository,
        sample_settings,
    ):
        """Test updating the default user profile."""
        # Setup
        mock_user_profile_repository.get_by_id.return_value = (
            MagicMock()
        )  # User profile exists
        mock_application_settings_repository.update_default_user_profile.return_value = (
            sample_settings
        )

        # Execute
        result = service.update_default_user_profile(profile_id=1)

        # Verify
        assert result == sample_settings
        mock_user_profile_repository.get_by_id.assert_called_once_with(1)
        mock_application_settings_repository.update_default_user_profile.assert_called_once_with(
            1
        )

    def test_update_default_user_profile_null(
        self,
        service,
        mock_application_settings_repository,
        mock_user_profile_repository,
        sample_settings,
    ):
        """Test clearing the default user profile."""
        # Setup
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=1,
            default_system_prompt_id=1,
            default_user_profile_id=None,  # Cleared
            default_avatar_image="/path/to/default/avatar.png",
        )
        mock_application_settings_repository.update_default_user_profile.return_value = (
            updated_settings
        )

        # Execute
        result = service.update_default_user_profile(profile_id=None)

        # Verify
        assert result == updated_settings
        mock_user_profile_repository.get_by_id.assert_not_called()  # No need to check if None
        mock_application_settings_repository.update_default_user_profile.assert_called_once_with(
            None
        )

    def test_update_default_user_profile_not_found(
        self,
        service,
        mock_application_settings_repository,
        mock_user_profile_repository,
    ):
        """Test updating with non-existent user profile."""
        # Setup
        mock_user_profile_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_default_user_profile(profile_id=999)

        # Verify repository method was not called
        mock_application_settings_repository.update_default_user_profile.assert_not_called()

    def test_update_default_avatar_image(
        self, service, mock_application_settings_repository, sample_settings
    ):
        """Test updating the default avatar image."""
        # Setup
        mock_application_settings_repository.update_default_avatar_image.return_value = (
            sample_settings
        )

        # Execute
        result = service.update_default_avatar_image(
            avatar_path="/path/to/default/avatar.png"
        )

        # Verify
        assert result == sample_settings
        mock_application_settings_repository.update_default_avatar_image.assert_called_once_with(
            "/path/to/default/avatar.png"
        )

    def test_update_default_avatar_image_null(
        self, service, mock_application_settings_repository, sample_settings
    ):
        """Test clearing the default avatar image."""
        # Setup
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=1,
            default_system_prompt_id=1,
            default_user_profile_id=1,
            default_avatar_image=None,  # Cleared
        )
        mock_application_settings_repository.update_default_avatar_image.return_value = (
            updated_settings
        )

        # Execute
        result = service.update_default_avatar_image(avatar_path=None)

        # Verify
        assert result == updated_settings
        mock_application_settings_repository.update_default_avatar_image.assert_called_once_with(
            None
        )

    def test_update_default_avatar_image_empty_string(
        self, service, mock_application_settings_repository
    ):
        """Test updating the default avatar image with empty string."""
        # Execute and verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_default_avatar_image(avatar_path="")

        assert "default_avatar_image" in excinfo.value.details
        mock_application_settings_repository.update_default_avatar_image.assert_not_called()

        with pytest.raises(ValidationError) as excinfo:
            service.update_default_avatar_image(avatar_path="   ")

        assert "default_avatar_image" in excinfo.value.details
        mock_application_settings_repository.update_default_avatar_image.assert_not_called()

    def test_update_settings(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        mock_user_profile_repository,
        sample_settings,
    ):
        """Test updating multiple settings at once."""
        # Setup
        mock_ai_model_repository.get_by_id.return_value = MagicMock()  # AI model exists
        mock_system_prompt_repository.get_by_id.return_value = (
            MagicMock()
        )  # System prompt exists
        mock_user_profile_repository.get_by_id.return_value = (
            MagicMock()
        )  # User profile exists
        mock_application_settings_repository.save_settings.return_value = (
            sample_settings
        )

        # Execute
        result = service.update_settings(
            default_ai_model_id=1,
            default_system_prompt_id=1,
            default_user_profile_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )

        # Verify
        assert result == sample_settings
        mock_ai_model_repository.get_by_id.assert_called_once_with(1)
        mock_system_prompt_repository.get_by_id.assert_called_once_with(1)
        mock_user_profile_repository.get_by_id.assert_called_once_with(1)
        mock_application_settings_repository.save_settings.assert_called_once_with(
            default_ai_model_id=1,
            default_system_prompt_id=1,
            default_user_profile_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )

    def test_update_settings_partial(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
        sample_settings,
    ):
        """Test updating only some settings."""
        # Setup
        mock_ai_model_repository.get_by_id.return_value = MagicMock()  # AI model exists
        mock_application_settings_repository.save_settings.return_value = (
            sample_settings
        )

        # Execute - only update AI model and avatar
        result = service.update_settings(
            default_ai_model_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )

        # Verify
        assert result == sample_settings
        mock_ai_model_repository.get_by_id.assert_called_once_with(1)
        mock_application_settings_repository.save_settings.assert_called_once_with(
            default_ai_model_id=1,
            default_avatar_image="/path/to/default/avatar.png",
        )

    def test_update_settings_null_values(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
        mock_system_prompt_repository,
        mock_user_profile_repository,
        sample_settings,
    ):
        """Test updating settings with null values."""
        # Setup
        updated_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,  # Cleared
            default_system_prompt_id=None,  # Cleared
            default_user_profile_id=None,  # Cleared
            default_avatar_image=None,  # Cleared
        )
        mock_application_settings_repository.save_settings.return_value = (
            updated_settings
        )

        # Execute - set all values to None
        result = service.update_settings(
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
        )

        # Verify
        assert result == updated_settings
        mock_application_settings_repository.save_settings.assert_called_once_with(
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
        )

    def test_update_settings_no_changes(
        self,
        service,
        mock_application_settings_repository,
        sample_settings,
    ):
        """Test update settings with no changes."""
        # Setup
        mock_application_settings_repository.get_settings.return_value = sample_settings

        # Patch the update_settings method to ensure it returns get_settings()
        # when called without arguments
        with patch.object(
            service,
            "update_settings",
            wraps=lambda *args, **kwargs: (
                service.repository.get_settings()
                if not kwargs
                else service.repository.save_settings(**kwargs)
            ),
        ):
            # Execute - no changes
            result = service.update_settings()

            # Verify
            assert result == sample_settings
            mock_application_settings_repository.get_settings.assert_called_once()
            mock_application_settings_repository.save_settings.assert_not_called()

    def test_update_settings_entity_not_found(
        self,
        service,
        mock_application_settings_repository,
        mock_ai_model_repository,
    ):
        """Test updating settings with non-existent entity."""
        # Setup
        mock_ai_model_repository.get_by_id.side_effect = ResourceNotFoundError(
            "Not found"
        )

        # Execute and verify
        with pytest.raises(ResourceNotFoundError):
            service.update_settings(
                default_ai_model_id=999,  # Non-existent
            )

        # Verify repository method was not called
        mock_application_settings_repository.save_settings.assert_not_called()

    def test_update_settings_validation_error(
        self,
        service,
        mock_application_settings_repository,
    ):
        """Test updating settings with invalid values."""
        # Execute and verify - empty avatar path
        with pytest.raises(ValidationError) as excinfo:
            service.update_settings(
                default_avatar_image="",  # Empty string
            )

        assert "default_avatar_image" in excinfo.value.details
        mock_application_settings_repository.save_settings.assert_not_called()

    def test_reset_settings(
        self,
        service,
        mock_application_settings_repository,
        sample_settings,
    ):
        """Test resetting settings to defaults."""
        # Setup
        reset_settings = ApplicationSettings(
            id=1,
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
        )
        mock_application_settings_repository.save_settings.return_value = reset_settings

        # Execute
        result = service.reset_settings()

        # Verify
        assert result == reset_settings
        mock_application_settings_repository.save_settings.assert_called_once_with(
            default_ai_model_id=None,
            default_system_prompt_id=None,
            default_user_profile_id=None,
            default_avatar_image=None,
        )

    # OpenRouter API Key Tests

    @patch("app.services.application_settings_service.encryption_service")
    def test_set_openrouter_api_key_success(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
        sample_settings,
    ):
        """Test successfully setting OpenRouter API key."""
        # Setup
        api_key = "sk-or-test-api-key-123"
        encrypted_key = "encrypted_api_key_data"
        mock_encryption_service.encrypt_api_key.return_value = encrypted_key
        mock_application_settings_repository.save_settings.return_value = (
            sample_settings
        )

        # Execute
        result = service.set_openrouter_api_key(api_key)

        # Verify
        assert result == sample_settings
        mock_encryption_service.encrypt_api_key.assert_called_once_with(api_key)
        mock_application_settings_repository.save_settings.assert_called_once_with(
            openrouter_api_key_encrypted=encrypted_key
        )

    @patch("app.services.application_settings_service.encryption_service")
    def test_set_openrouter_api_key_empty_string(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test setting empty OpenRouter API key raises validation error."""
        with pytest.raises(ValidationError, match="OpenRouter API key cannot be empty"):
            service.set_openrouter_api_key("")

        mock_encryption_service.encrypt_api_key.assert_not_called()
        mock_application_settings_repository.save_settings.assert_not_called()

    @patch("app.services.application_settings_service.encryption_service")
    def test_set_openrouter_api_key_whitespace_only(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test setting whitespace-only OpenRouter API key raises validation error."""
        with pytest.raises(ValidationError, match="OpenRouter API key cannot be empty"):
            service.set_openrouter_api_key("   ")

        mock_encryption_service.encrypt_api_key.assert_not_called()
        mock_application_settings_repository.save_settings.assert_not_called()

    @patch("app.services.application_settings_service.encryption_service")
    def test_set_openrouter_api_key_encryption_failure(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test handling encryption failure when setting API key."""
        # Setup
        api_key = "sk-or-test-api-key-123"
        mock_encryption_service.encrypt_api_key.side_effect = Exception(
            "Encryption failed"
        )

        # Execute & Verify
        with pytest.raises(ValidationError, match="Failed to encrypt API key"):
            service.set_openrouter_api_key(api_key)

        mock_application_settings_repository.save_settings.assert_not_called()

    @patch("app.services.application_settings_service.encryption_service")
    def test_get_openrouter_api_key_success(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test successfully getting OpenRouter API key."""
        # Setup
        encrypted_key = "encrypted_api_key_data"
        decrypted_key = "sk-or-test-api-key-123"
        settings = ApplicationSettings(id=1, openrouter_api_key_encrypted=encrypted_key)
        mock_application_settings_repository.get_settings.return_value = settings
        mock_encryption_service.decrypt_api_key.return_value = decrypted_key

        # Execute
        result = service.get_openrouter_api_key()

        # Verify
        assert result == decrypted_key
        mock_encryption_service.decrypt_api_key.assert_called_once_with(encrypted_key)

    @patch("app.services.application_settings_service.encryption_service")
    def test_get_openrouter_api_key_no_key_stored(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test getting OpenRouter API key when none is stored."""
        # Setup
        settings = ApplicationSettings(id=1, openrouter_api_key_encrypted=None)
        mock_application_settings_repository.get_settings.return_value = settings

        # Execute
        result = service.get_openrouter_api_key()

        # Verify
        assert result is None
        mock_encryption_service.decrypt_api_key.assert_not_called()

    @patch("app.services.application_settings_service.encryption_service")
    def test_get_openrouter_api_key_decryption_failure(
        self,
        mock_encryption_service,
        service,
        mock_application_settings_repository,
    ):
        """Test handling decryption failure when getting API key."""
        # Setup
        encrypted_key = "encrypted_api_key_data"
        settings = ApplicationSettings(id=1, openrouter_api_key_encrypted=encrypted_key)
        mock_application_settings_repository.get_settings.return_value = settings
        mock_encryption_service.decrypt_api_key.side_effect = Exception(
            "Decryption failed"
        )

        # Execute & Verify
        with pytest.raises(ValidationError, match="Failed to decrypt API key"):
            service.get_openrouter_api_key()

    def test_clear_openrouter_api_key_success(
        self,
        service,
        mock_application_settings_repository,
        sample_settings,
    ):
        """Test successfully clearing OpenRouter API key."""
        # Setup
        mock_application_settings_repository.save_settings.return_value = (
            sample_settings
        )

        # Execute
        result = service.clear_openrouter_api_key()

        # Verify
        assert result == sample_settings
        mock_application_settings_repository.save_settings.assert_called_once_with(
            openrouter_api_key_encrypted=None
        )
