"""Tests for the ApplicationSettingsRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.application_settings import ApplicationSettings
from app.repositories.application_settings_repository import (
    ApplicationSettingsRepository,
)
from app.utils.exceptions import DatabaseError


class TestApplicationSettingsRepository:
    """Test application settings repository functionality."""

    def test_get_settings_creates_if_not_exists(self, db_session):
        """Test that get_settings creates a new settings record if one doesn't exist."""
        repo = ApplicationSettingsRepository(db_session)

        # Verify no settings exist yet
        existing_settings = db_session.query(ApplicationSettings).first()
        assert existing_settings is None

        # Get settings - should create a new record
        settings = repo.get_settings()
        db_session.commit()

        # Verify settings were created
        assert settings is not None
        assert settings.id == 1  # Singleton ID
        assert settings.default_ai_model_id is None
        assert settings.default_system_prompt_id is None
        assert settings.default_user_profile_id is None
        assert settings.default_avatar_image is None

    def test_get_settings_returns_existing(self, db_session):
        """Test that get_settings returns existing settings."""
        repo = ApplicationSettingsRepository(db_session)

        # Create settings
        settings = repo.get_settings()
        # Set a value to identify it
        settings.default_avatar_image = "test_avatar.png"
        db_session.commit()

        # Get settings again - should return the same record
        settings2 = repo.get_settings()

        # Verify the same settings were returned
        assert settings2 is not None
        assert settings2.id == settings.id
        assert settings2.default_avatar_image == "test_avatar.png"

    def test_save_settings(
        self,
        db_session,
        create_character,
        create_user_profile,
        create_ai_model,
        create_system_prompt,
    ):
        """Test saving application settings."""
        repo = ApplicationSettingsRepository(db_session)

        # Create entities to reference
        character = create_character(label="settings_test_char")
        user_profile = create_user_profile(label="settings_test_profile")
        ai_model = create_ai_model(label="settings_test_model")
        system_prompt = create_system_prompt(label="settings_test_prompt")

        db_session.add_all([character, user_profile, ai_model, system_prompt])
        db_session.flush()

        # Save settings
        settings = repo.save_settings(
            default_ai_model_id=ai_model.id,
            default_system_prompt_id=system_prompt.id,
            default_user_profile_id=user_profile.id,
            default_avatar_image="test_avatar.png",
        )
        db_session.commit()

        # Verify settings were saved
        assert settings is not None
        assert settings.default_ai_model_id == ai_model.id
        assert settings.default_system_prompt_id == system_prompt.id
        assert settings.default_user_profile_id == user_profile.id
        assert settings.default_avatar_image == "test_avatar.png"

        # Get settings to verify they're saved
        db_settings = db_session.query(ApplicationSettings).first()
        assert db_settings is not None
        assert db_settings.default_ai_model_id == ai_model.id

    def test_update_helper_methods(
        self,
        db_session,
        create_character,
        create_user_profile,
        create_ai_model,
        create_system_prompt,
    ):
        """Test helper methods for updating specific settings."""
        repo = ApplicationSettingsRepository(db_session)

        # Create entities to reference
        character = create_character(label="helpers_test_char")
        user_profile = create_user_profile(label="helpers_test_profile")
        ai_model = create_ai_model(label="helpers_test_model")
        system_prompt = create_system_prompt(label="helpers_test_prompt")

        db_session.add_all([character, user_profile, ai_model, system_prompt])
        db_session.flush()

        # Test update methods
        repo.update_default_ai_model(ai_model.id)
        repo.update_default_system_prompt(system_prompt.id)
        repo.update_default_user_profile(user_profile.id)
        repo.update_default_avatar_image("helper_avatar.png")
        db_session.commit()

        # Get settings to verify updates
        settings = repo.get_settings()
        assert settings.default_ai_model_id == ai_model.id
        assert settings.default_system_prompt_id == system_prompt.id
        assert settings.default_user_profile_id == user_profile.id
        assert settings.default_avatar_image == "helper_avatar.png"

        # Test clearing settings
        repo.update_default_ai_model(None)
        db_session.commit()

        # Verify setting was cleared
        settings = repo.get_settings()
        assert settings.default_ai_model_id is None

    def test_caching_mechanism_exists(self, db_session):
        """Simple test to verify caching mechanism exists.

        Note: This test doesn't verify the actual caching behavior,
        just confirms that the caching infrastructure is in place.
        """
        repo = ApplicationSettingsRepository(db_session)

        # Verify that the caching decorator is applied
        assert hasattr(repo, "_cached_get_settings")

        # Test cache clear functionality exists and doesn't raise errors
        try:
            repo._cached_get_settings.cache_clear()
        except Exception as e:
            pytest.fail(f"Cache clearing failed: {e}")

    def test_database_error_handling(self, db_session):
        """Test handling of database errors in application settings repository methods."""
        repo = ApplicationSettingsRepository(db_session)

        # To ensure the cache doesn't interfere with error testing
        repo._cached_get_settings.cache_clear()

        # Mock ApplicationSettings.get_instance to raise SQLAlchemyError
        with patch(
            "app.models.application_settings.ApplicationSettings.get_instance",
            side_effect=SQLAlchemyError("Test error"),
        ):
            with pytest.raises(DatabaseError):
                repo._get_settings_impl()  # Test the implementation directly

        # Test error in save_settings
        # Get a valid settings object first to work with
        repo.get_settings()
        db_session.commit()

        # Mock the session to raise errors on flush
        with patch.object(
            db_session, "flush", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.save_settings(default_avatar_image="error_test.png")
