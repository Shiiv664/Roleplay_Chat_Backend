"""Tests for the ApplicationSettings model using helper functions."""

import pytest
from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.exc import IntegrityError

from app.models.application_settings import ApplicationSettings
from app.models.base import Base
from tests.models.helpers import (
    check_column_constraints,
    check_foreign_key_constraint,
    check_model_columns_existence,
    check_model_inheritance,
    check_model_repr,
    check_model_tablename,
    check_relationship,
)


def test_application_settings_inheritance():
    """Test ApplicationSettings model inherits from correct base class."""
    check_model_inheritance(ApplicationSettings, Base)


def test_application_settings_tablename():
    """Test ApplicationSettings model has the correct table name."""
    check_model_tablename(ApplicationSettings, "applicationSettings")


def test_application_settings_columns():
    """Test ApplicationSettings model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "default_ai_model_id",
        "default_system_prompt_id",
        "default_user_profile_id",
        "default_avatar_image",
        "default_ai_model",
        "default_system_prompt",
        "default_user_profile",
    ]
    check_model_columns_existence(ApplicationSettings, expected_columns)

    # Test column constraints
    check_column_constraints(
        ApplicationSettings, "id", nullable=False, primary_key=True, column_type=Integer
    )

    check_column_constraints(
        ApplicationSettings, "default_ai_model_id", nullable=True, column_type=Integer
    )

    check_column_constraints(
        ApplicationSettings,
        "default_system_prompt_id",
        nullable=True,
        column_type=Integer,
    )

    check_column_constraints(
        ApplicationSettings,
        "default_user_profile_id",
        nullable=True,
        column_type=Integer,
    )

    check_column_constraints(
        ApplicationSettings, "default_avatar_image", nullable=True, column_type=String
    )

    # Verify the table has a check constraint for singleton pattern
    # Debug to understand the structure of __table_args__
    singleton_constraint_found = False

    # Check if 'name' is in the __table_args__ dictionary (named tuple case)
    for constraint in ApplicationSettings.__table__.constraints:
        if (
            isinstance(constraint, CheckConstraint)
            and constraint.name == "application_settings_singleton"
        ):
            singleton_constraint_found = True
            break

    assert singleton_constraint_found, (
        "Application settings should have a check constraint to enforce the singleton "
        "pattern"
    )


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

    # Create a factory function for creating valid settings
    def create_valid_settings(**kwargs):
        valid_fields = {
            "default_ai_model_id": ai_model.id,
            "default_system_prompt_id": system_prompt.id,
            "default_user_profile_id": user_profile.id,
        }
        valid_fields.update(kwargs)
        return ApplicationSettings(**valid_fields)

    # Test ai_model_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_settings,
        fk_field="default_ai_model_id",
        invalid_id=999999,  # Non-existent ID
    )

    # Test system_prompt_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_settings,
        fk_field="default_system_prompt_id",
        invalid_id=999999,  # Non-existent ID
    )

    # Test user_profile_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_settings,
        fk_field="default_user_profile_id",
        invalid_id=999999,  # Non-existent ID
    )


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

    # Test relationship with ai_model using helper
    check_relationship(
        db_session=db_session,
        parent_obj=settings,
        child_obj=ai_model,
        parent_attr="default_ai_model",
        child_attr="default_in_settings",
        is_collection=False,
        bidirectional=True,
    )

    # Test relationship with system_prompt using helper
    check_relationship(
        db_session=db_session,
        parent_obj=settings,
        child_obj=system_prompt,
        parent_attr="default_system_prompt",
        child_attr="default_in_settings",
        is_collection=False,
        bidirectional=True,
    )

    # Test relationship with user_profile using helper
    check_relationship(
        db_session=db_session,
        parent_obj=settings,
        child_obj=user_profile,
        parent_attr="default_user_profile",
        child_attr="default_in_settings",
        is_collection=False,
        bidirectional=True,
    )


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

    # Test representation using helper
    expected_attrs = {"id": 1}

    check_model_repr(settings, expected_attrs)
