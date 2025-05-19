"""Tests for the UserProfile model using helper functions."""

from sqlalchemy import Integer, String, Text

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base, TimestampMixin
from app.models.user_profile import UserProfile
from tests.models.helpers import (
    check_model_inheritance,
    check_model_tablename,
    check_model_columns_existence,
    check_model_repr,
    check_column_constraints,
    check_unique_constraint,
    check_relationship,
)


def test_user_profile_inheritance():
    """Test UserProfile model inherits from correct base classes."""
    check_model_inheritance(UserProfile, Base)
    check_model_inheritance(UserProfile, TimestampMixin)


def test_user_profile_tablename():
    """Test UserProfile model has the correct table name."""
    check_model_tablename(UserProfile, "userProfile")


def test_user_profile_columns():
    """Test UserProfile model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "label",
        "name",
        "avatar_image",
        "description",
        "created_at",
        "updated_at",
        "chat_sessions",
        "default_in_settings",
    ]
    check_model_columns_existence(UserProfile, expected_columns)
    
    # Test column constraints
    check_column_constraints(
        UserProfile, "id", nullable=False, primary_key=True, column_type=Integer
    )
    
    check_column_constraints(
        UserProfile, "label", nullable=False, unique=True, column_type=String
    )
    
    check_column_constraints(
        UserProfile, "name", nullable=False, column_type=String
    )
    
    check_column_constraints(
        UserProfile, "description", nullable=True, column_type=Text
    )
    
    check_column_constraints(
        UserProfile, "avatar_image", nullable=True, column_type=String
    )


def test_user_profile_initialization(create_user_profile):
    """Test UserProfile model initialization with valid data."""
    # Create with default values
    user_profile = create_user_profile()

    assert user_profile.label == "test_profile"
    assert user_profile.name == "Test User"
    assert user_profile.description == "A test user profile"
    assert user_profile.avatar_image is None

    # Create with custom values
    custom_profile = create_user_profile(
        label="custom_profile",
        name="Custom User",
        description="Custom description",
        avatar_image="custom.png",
    )

    assert custom_profile.label == "custom_profile"
    assert custom_profile.name == "Custom User"
    assert custom_profile.description == "Custom description"
    assert custom_profile.avatar_image == "custom.png"


def test_user_profile_required_fields(db_session):
    """Test UserProfile model required fields."""
    # Test missing label
    profile_no_label = UserProfile(name="No Label Profile")
    db_session.add(profile_no_label)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing name
    profile_no_name = UserProfile(label="no_name_profile")
    db_session.add(profile_no_name)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_profile_unique_constraint(db_session, create_user_profile):
    """Test UserProfile model label uniqueness constraint."""
    # Create a function that creates profiles with a specific label
    def create_profile_with_label(label_value):
        return create_user_profile(label=label_value)
    
    # Test the unique constraint on the label field
    check_unique_constraint(
        db_session=db_session,
        model_class=UserProfile,
        create_instance_with_unique=create_profile_with_label,
        unique_field="label"
    )


def test_user_profile_optional_fields(db_session):
    """Test UserProfile model optional fields."""
    # Create profile with minimal required fields
    profile = UserProfile(label="minimal", name="Minimal Profile")
    db_session.add(profile)
    db_session.commit()

    # Verify optional fields are None
    assert profile.description is None
    assert profile.avatar_image is None


def test_user_profile_representation(create_user_profile):
    """Test UserProfile model string representation."""
    profile = create_user_profile()
    profile.id = 1  # Set ID manually for testing

    # Test representation using helper
    expected_attrs = {
        "id": 1,
        "label": "'test_profile'",
        "name": "'Test User'"
    }
    
    check_model_repr(profile, expected_attrs)


def test_user_profile_relationships(
    db_session, create_user_profile, create_chat_session, create_character
):
    """Test UserProfile model relationships with chat sessions."""
    # Create and save a user profile
    profile = create_user_profile()
    db_session.add(profile)
    db_session.commit()

    # Create a character for the chat session
    character = create_character(label=f"char_for_user_profile_{profile.id}")
    db_session.add(character)
    db_session.commit()

    # Create a chat session associated with the profile
    session = create_chat_session(user_profile=profile, character=character)
    db_session.add(session)
    db_session.commit()

    # Test relationship using helper
    check_relationship(
        db_session=db_session,
        parent_obj=profile,
        child_obj=session,
        parent_attr="chat_sessions",
        child_attr="user_profile",
        is_collection=True,
        bidirectional=True
    )
    
    # Create a second session to verify multiple relationships
    character2 = create_character(label=f"char_for_user_profile_2_{profile.id}")
    db_session.add(character2)
    db_session.commit()
    
    session2 = create_chat_session(user_profile=profile, character=character2)
    db_session.add(session2)
    db_session.commit()
    
    # Verify multiple sessions
    sessions = profile.chat_sessions.all()
    assert len(sessions) == 2