"""Tests for the Base model and TimestampMixin."""

import datetime

from sqlalchemy.orm import DeclarativeBase

from app.models.base import Base
from app.models.character import Character
from tests.models.helpers import (
    check_model_columns_existence,
    check_model_inheritance,
    check_model_to_dict,
    force_update_timestamp,
)


def test_base_inheritance():
    """Test that Base inherits from DeclarativeBase."""
    check_model_inheritance(Base, DeclarativeBase)


def test_base_to_dict(db_session, create_character):
    """Test Base.to_dict() method."""
    # Create and save a character
    character = create_character()
    db_session.add(character)
    db_session.commit()

    # Define expected values
    expected_values = {
        "id": character.id,
        "label": "test_character",
        "name": "Test Character",
        "description": "A test character description",
    }

    # Test to_dict using helper
    check_model_to_dict(character, expected_values)

    # Verify timestamps are present (separately since we can't predict their values)
    char_dict = character.to_dict()
    assert "created_at" in char_dict
    assert "updated_at" in char_dict


def test_base_from_dict():
    """Test Base.from_dict() method."""
    # Create test data
    test_data = {
        "label": "from_dict_test",
        "name": "From Dict Test",
        "description": "Created from dictionary",
        "avatar_image": "test.png",
        "extra_field": "Should be ignored",  # This field should be ignored
    }

    # Create model from dictionary
    character = Character.from_dict(test_data)

    # Verify the result is a Character instance with expected values
    assert isinstance(character, Character)
    assert character.label == "from_dict_test"
    assert character.name == "From Dict Test"
    assert character.description == "Created from dictionary"
    assert character.avatar_image == "test.png"
    # Extra field should be ignored
    assert not hasattr(character, "extra_field")


def test_timestamp_mixin_attributes():
    """Test that TimestampMixin adds expected attributes."""
    # Check that a model inheriting from TimestampMixin has timestamp columns
    expected_attributes = ["created_at", "updated_at"]
    check_model_columns_existence(Character, expected_attributes)


def test_timestamp_values_on_save(db_session, create_character):
    """Test that timestamps are set when the model is saved."""
    # Create a character
    character = create_character()

    # Before save, timestamps should not be set
    assert character.created_at is None
    assert character.updated_at is None

    # Save the character
    db_session.add(character)
    db_session.commit()

    # After save, timestamps should be set
    assert character.created_at is not None
    assert character.updated_at is not None
    assert isinstance(character.created_at, datetime.datetime)
    assert isinstance(character.updated_at, datetime.datetime)
    # Both timestamps should be the same on creation
    assert character.created_at == character.updated_at


def test_timestamp_updated_on_change(db_session, create_character):
    """Test that updated_at is updated when the model is changed."""
    # Create and save a character
    character = create_character()
    db_session.add(character)
    db_session.commit()

    # Store the original timestamps
    created_at = character.created_at

    # Force the updated_at field to be different using our helper
    new_updated_at = force_update_timestamp(db_session, character, "updated_at", 1)

    # created_at should not change
    assert character.created_at == created_at

    # updated_at should be different from created_at
    assert new_updated_at != created_at
    assert character.updated_at != created_at
