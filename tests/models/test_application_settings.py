"""Tests for the ApplicationSettings model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.application_settings import ApplicationSettings
from app.models.base import Base


def test_application_settings_inheritance():
    """Test ApplicationSettings model inherits from correct base class."""
    assert issubclass(ApplicationSettings, Base)


def test_application_settings_tablename():
    """Test ApplicationSettings model has the correct table name."""
    assert ApplicationSettings.__tablename__ == "applicationSettings"


def test_application_settings_columns():
    """Test ApplicationSettings model has the expected columns."""
    # Check primary key
    assert hasattr(ApplicationSettings, "id")

    # Check foreign key fields
    assert hasattr(ApplicationSettings, "default_ai_model_id")
    assert hasattr(ApplicationSettings, "default_system_prompt_id")
    assert hasattr(ApplicationSettings, "default_user_profile_id")

    # Check other fields
    assert hasattr(ApplicationSettings, "default_avatar_image")

    # Check relationships
    assert hasattr(ApplicationSettings, "default_ai_model")
    assert hasattr(ApplicationSettings, "default_system_prompt")
    assert hasattr(ApplicationSettings, "default_user_profile")


def test_application_settings_initialization(db_session):
    """Test ApplicationSettings model initialization with minimal data."""
    settings = ApplicationSettings()

    # Verify values before save
    assert settings.default_ai_model_id is None
    assert settings.default_system_prompt_id is None
    assert settings.default_user_profile_id is None
    assert settings.default_avatar_image is None

    # After adding to session and committing, id should be 1
    db_session.add(settings)
    db_session.commit()
    assert settings.id == 1


def test_application_settings_initialization_with_data(
    db_session, create_ai_model, create_system_prompt, create_user_profile
):
    """Test ApplicationSettings model initialization with all fields."""
    # Create related entities
    ai_model = create_ai_model(label="app_settings_test_model")
    system_prompt = create_system_prompt(label="app_settings_test_prompt")
    user_profile = create_user_profile(label="app_settings_test_profile")

    db_session.add_all([ai_model, system_prompt, user_profile])
    db_session.commit()

    # Create application settings with all fields
    settings = ApplicationSettings(
        default_ai_model_id=ai_model.id,
        default_system_prompt_id=system_prompt.id,
        default_user_profile_id=user_profile.id,
        default_avatar_image="/path/to/default/avatar.png",
    )

    # Verify field values before save
    assert settings.default_ai_model_id == ai_model.id
    assert settings.default_system_prompt_id == system_prompt.id
    assert settings.default_user_profile_id == user_profile.id
    assert settings.default_avatar_image == "/path/to/default/avatar.png"

    # After adding to session and committing, id should be 1
    db_session.add(settings)
    db_session.commit()
    assert settings.id == 1


def test_application_settings_singleton_constraint(db_session):
    """Test ApplicationSettings enforces singleton pattern through id constraint."""
    # Create first instance
    settings1 = ApplicationSettings()
    db_session.add(settings1)
    db_session.commit()

    # Create second instance with id=1 (should fail)
    settings2 = ApplicationSettings()
    db_session.add(settings2)

    # Should raise IntegrityError due to unique constraint on id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Create instance with different id (should fail due to check constraint)
    settings3 = ApplicationSettings(id=2)
    db_session.add(settings3)

    # Should raise IntegrityError due to check constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_application_settings_get_instance(db_session):
    """Test ApplicationSettings.get_instance class method."""
    # No instance exists yet
    settings = ApplicationSettings.get_instance(db_session)

    # Should create and return a new instance
    assert settings is not None
    assert settings.id == 1

    # Verify instance was saved
    db_session.commit()
    settings_from_db = db_session.query(ApplicationSettings).first()
    assert settings_from_db is not None
    assert settings_from_db.id == 1

    # Get instance again, should return existing one
    settings2 = ApplicationSettings.get_instance(db_session)
    assert settings2 is settings_from_db


def test_application_settings_foreign_key_constraints(
    db_session, create_ai_model, create_system_prompt, create_user_profile
):
    """Test ApplicationSettings model foreign key constraints."""
    # Create related entities
    ai_model = create_ai_model(label="fk_test_model")
    system_prompt = create_system_prompt(label="fk_test_prompt")
    user_profile = create_user_profile(label="fk_test_profile")

    db_session.add_all([ai_model, system_prompt, user_profile])
    db_session.commit()

    # Test valid foreign keys
    settings = ApplicationSettings(
        default_ai_model_id=ai_model.id,
        default_system_prompt_id=system_prompt.id,
        default_user_profile_id=user_profile.id,
    )
    db_session.add(settings)
    db_session.commit()

    # Test invalid foreign key for ai_model_id
    invalid_model_id = 999999  # Non-existent ID
    settings.default_ai_model_id = invalid_model_id

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Reset to valid state
    settings = db_session.query(ApplicationSettings).first()

    # Test invalid foreign key for system_prompt_id
    invalid_prompt_id = 999999  # Non-existent ID
    settings.default_system_prompt_id = invalid_prompt_id

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_application_settings_relationships(
    db_session, create_ai_model, create_system_prompt, create_user_profile
):
    """Test ApplicationSettings model relationships."""
    # Create related entities
    ai_model = create_ai_model(label="rel_test_model")
    system_prompt = create_system_prompt(label="rel_test_prompt")
    user_profile = create_user_profile(label="rel_test_profile")

    db_session.add_all([ai_model, system_prompt, user_profile])
    db_session.commit()

    # Create application settings
    settings = ApplicationSettings(
        default_ai_model_id=ai_model.id,
        default_system_prompt_id=system_prompt.id,
        default_user_profile_id=user_profile.id,
    )
    db_session.add(settings)
    db_session.commit()

    # Test relationship with ai_model
    assert settings.default_ai_model.id == ai_model.id
    assert settings.default_ai_model.label == ai_model.label

    # Test relationship with system_prompt
    assert settings.default_system_prompt.id == system_prompt.id
    assert settings.default_system_prompt.label == system_prompt.label

    # Test relationship with user_profile
    assert settings.default_user_profile.id == user_profile.id
    assert settings.default_user_profile.label == user_profile.label

    # Test bidirectional relationships - these are one-to-one relationships, not lists
    assert settings == ai_model.default_in_settings
    assert settings == system_prompt.default_in_settings
    assert settings == user_profile.default_in_settings


def test_application_settings_nullability(db_session):
    """Test ApplicationSettings foreign keys can be null."""
    # Create settings with null foreign keys
    settings = ApplicationSettings()
    db_session.add(settings)
    db_session.commit()

    # Verify null values are allowed
    assert settings.default_ai_model_id is None
    assert settings.default_system_prompt_id is None
    assert settings.default_user_profile_id is None
    assert settings.default_avatar_image is None


def test_application_settings_representation(db_session):
    """Test ApplicationSettings model string representation."""
    # Create settings
    settings = ApplicationSettings()
    db_session.add(settings)
    db_session.commit()

    # Test __repr__ method
    repr_string = repr(settings)
    assert "ApplicationSettings" in repr_string
    assert "id=1" in repr_string
