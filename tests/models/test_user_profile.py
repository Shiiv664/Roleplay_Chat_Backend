"""Tests for the UserProfile model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base, TimestampMixin
from app.models.user_profile import UserProfile


def test_user_profile_inheritance():
    """Test UserProfile model inherits from correct base classes."""
    assert issubclass(UserProfile, Base)
    assert issubclass(UserProfile, TimestampMixin)


def test_user_profile_tablename():
    """Test UserProfile model has the correct table name."""
    assert UserProfile.__tablename__ == "userProfile"


def test_user_profile_columns():
    """Test UserProfile model has the expected columns."""
    # Check primary key
    assert hasattr(UserProfile, "id")

    # Check required columns
    assert hasattr(UserProfile, "label")
    assert hasattr(UserProfile, "name")

    # Check optional columns
    assert hasattr(UserProfile, "avatar_image")
    assert hasattr(UserProfile, "description")

    # Check timestamp columns from mixin
    assert hasattr(UserProfile, "created_at")
    assert hasattr(UserProfile, "updated_at")

    # Check relationships
    assert hasattr(UserProfile, "chat_sessions")
    assert hasattr(UserProfile, "default_in_settings")


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
    # Create and save first profile
    profile1 = create_user_profile(label="unique_test")
    db_session.add(profile1)
    db_session.commit()

    # Try to create another profile with the same label
    profile2 = create_user_profile(label="unique_test", name="Duplicate Label")
    db_session.add(profile2)

    # Should raise IntegrityError due to unique constraint on label
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


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

    # Test __repr__ method
    repr_string = repr(profile)
    assert "UserProfile" in repr_string
    assert "test_profile" in repr_string
    assert "Test User" in repr_string


def test_user_profile_relationships(
    db_session, create_user_profile, create_chat_session, create_character
):
    """Test UserProfile model relationships with chat sessions."""
    # Create and save a user profile
    profile = create_user_profile()
    db_session.add(profile)
    db_session.commit()

    # Create characters with unique labels for each chat session
    character1 = create_character(label=f"char_for_user_profile_1_{profile.id}")
    character2 = create_character(label=f"char_for_user_profile_2_{profile.id}")
    db_session.add_all([character1, character2])
    db_session.commit()

    # Create chat sessions associated with the profile and unique characters
    session1 = create_chat_session(user_profile=profile, character=character1)
    session2 = create_chat_session(user_profile=profile, character=character2)
    db_session.add_all([session1, session2])
    db_session.commit()

    # Test relationship fetching
    sessions = profile.chat_sessions.all()
    assert len(sessions) == 2

    # Verify bidirectional relationship
    for session in sessions:
        assert session.user_profile_id == profile.id
