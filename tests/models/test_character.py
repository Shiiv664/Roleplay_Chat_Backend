"""Tests for the Character model using helper functions."""

import pytest
from sqlalchemy import Integer, String, Text
from sqlalchemy.exc import IntegrityError

from app.models.base import Base, TimestampMixin
from app.models.character import Character
from app.models.chat_session import ChatSession
from tests.models.helpers import (
    check_cascade_delete,
    check_column_constraints,
    check_model_columns_existence,
    check_model_inheritance,
    check_model_repr,
    check_model_tablename,
    check_relationship,
    check_unique_constraint,
)


def test_character_inheritance():
    """Test Character model inherits from correct base classes."""
    check_model_inheritance(Character, Base)
    check_model_inheritance(Character, TimestampMixin)


def test_character_tablename():
    """Test Character model has the correct table name."""
    check_model_tablename(Character, "character")


def test_character_columns():
    """Test Character model has the expected columns."""
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
    ]
    check_model_columns_existence(Character, expected_columns)

    # Test column constraints
    check_column_constraints(
        Character, "id", nullable=False, primary_key=True, column_type=Integer
    )

    check_column_constraints(
        Character, "label", nullable=False, unique=True, column_type=String
    )

    check_column_constraints(Character, "name", nullable=False, column_type=String)

    check_column_constraints(Character, "description", nullable=True, column_type=Text)

    check_column_constraints(
        Character, "avatar_image", nullable=True, column_type=String
    )


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

    # Create a function that creates characters with a specific label
    def create_character_with_label(label_value):
        return create_character(label=label_value)

    # Test the unique constraint on the label field
    check_unique_constraint(
        db_session=db_session,
        model_class=Character,
        create_instance_with_unique=create_character_with_label,
        unique_field="label",
    )


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
    character.id = 1  # Set ID manually for testing

    # Test representation using helper
    expected_attrs = {"id": 1, "label": "'test_character'", "name": "'Test Character'"}

    check_model_repr(character, expected_attrs)


def test_character_relationships(db_session, create_character, create_chat_session):
    """Test Character model relationships."""
    # Create and save a character
    character = create_character()
    db_session.add(character)
    db_session.commit()

    # Create a chat session associated with the character
    session = create_chat_session(character=character)
    db_session.add(session)
    db_session.commit()

    # Test relationship using helper
    check_relationship(
        db_session=db_session,
        parent_obj=character,
        child_obj=session,
        parent_attr="chat_sessions",
        child_attr="character",
        is_collection=True,
        bidirectional=True,
    )

    # Create a second session to verify multiple relationships
    session2 = create_chat_session(character=character)
    db_session.add(session2)
    db_session.commit()

    # Verify multiple sessions
    sessions = character.chat_sessions.all()
    assert len(sessions) == 2


def test_character_cascade_delete(db_session, create_character, create_chat_session):
    """Test Character cascade delete behavior with chat sessions."""
    # Create character and associated chat sessions
    character = create_character()
    db_session.add(character)
    db_session.commit()

    session1 = create_chat_session(character=character)
    db_session.add(session1)
    db_session.commit()

    # Test cascade delete using helper
    check_cascade_delete(
        db_session=db_session,
        parent_obj=character,
        child_obj=session1,
        parent_attr="chat_sessions",
        child_attr="character",
        child_class=ChatSession,
    )
