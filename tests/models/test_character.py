"""Tests for the Character model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base, TimestampMixin
from app.models.character import Character


def test_character_inheritance():
    """Test Character model inherits from correct base classes."""
    assert issubclass(Character, Base)
    assert issubclass(Character, TimestampMixin)


def test_character_tablename():
    """Test Character model has the correct table name."""
    assert Character.__tablename__ == "character"


def test_character_columns():
    """Test Character model has the expected columns."""
    # Check primary key
    assert hasattr(Character, "id")

    # Check required columns
    assert hasattr(Character, "label")
    assert hasattr(Character, "name")

    # Check optional columns
    assert hasattr(Character, "avatar_image")
    assert hasattr(Character, "description")

    # Check timestamp columns from mixin
    assert hasattr(Character, "created_at")
    assert hasattr(Character, "updated_at")

    # Check relationships
    assert hasattr(Character, "chat_sessions")


def test_character_initialization(create_character):
    """Test Character model initialization with valid data."""
    # Create with default values
    character = create_character()

    assert character.label == "test_character"
    assert character.name == "Test Character"
    assert character.description == "A test character description"
    assert character.avatar_image is None

    # Create with custom values
    custom_character = create_character(
        label="custom_character",
        name="Custom Character",
        description="Custom description",
        avatar_image="custom.png",
    )

    assert custom_character.label == "custom_character"
    assert custom_character.name == "Custom Character"
    assert custom_character.description == "Custom description"
    assert custom_character.avatar_image == "custom.png"


def test_character_required_fields(db_session):
    """Test Character model required fields."""
    # Test missing label
    character_no_label = Character(name="No Label Character")
    db_session.add(character_no_label)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing name
    character_no_name = Character(label="no_name_character")
    db_session.add(character_no_name)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_character_unique_constraint(db_session, create_character):
    """Test Character model label uniqueness constraint."""
    # Create and save first character
    character1 = create_character(label="unique_test")
    db_session.add(character1)
    db_session.commit()

    # Try to create another character with the same label
    character2 = create_character(label="unique_test", name="Duplicate Label")
    db_session.add(character2)

    # Should raise IntegrityError due to unique constraint on label
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_character_optional_fields(db_session, create_character):
    """Test Character model optional fields."""
    # Create character with minimal required fields
    character = Character(label="minimal", name="Minimal Character")
    db_session.add(character)
    db_session.commit()

    # Verify optional fields are None
    assert character.description is None
    assert character.avatar_image is None


def test_character_representation(create_character):
    """Test Character model string representation."""
    character = create_character()

    # Test __repr__ method
    repr_string = repr(character)
    assert "Character" in repr_string
    assert "test_character" in repr_string
    assert "Test Character" in repr_string


def test_character_relationships(db_session, create_character, create_chat_session):
    """Test Character model relationships."""
    # Create and save a character
    character = create_character()
    db_session.add(character)
    db_session.commit()

    # Create chat sessions associated with the character
    session1 = create_chat_session(character=character)
    session2 = create_chat_session(character=character)
    db_session.add_all([session1, session2])
    db_session.commit()

    # Test relationship fetching
    sessions = character.chat_sessions.all()
    assert len(sessions) == 2

    # Verify bidirectional relationship
    for session in sessions:
        assert session.character_id == character.id


def test_character_cascade_delete(db_session, create_character, create_chat_session):
    """Test Character cascade delete behavior with chat sessions."""
    # Create character and associated chat sessions
    character = create_character()
    db_session.add(character)
    db_session.commit()

    session1 = create_chat_session(character=character)
    db_session.add(session1)
    db_session.commit()

    # Store the session ID for verification
    session_id = session1.id

    # Delete the character
    db_session.delete(character)
    db_session.commit()

    # Verify the session was also deleted (cascade delete)
    from app.models.chat_session import ChatSession

    deleted_session = db_session.query(ChatSession).filter_by(id=session_id).first()
    assert deleted_session is None
