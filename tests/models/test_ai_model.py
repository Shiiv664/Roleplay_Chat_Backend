"""Tests for the AIModel model."""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ai_model import AIModel
from app.models.base import Base


def test_ai_model_inheritance():
    """Test AIModel model inherits from correct base class."""
    assert issubclass(AIModel, Base)
    # AIModel doesn't use TimestampMixin but has its own created_at


def test_ai_model_tablename():
    """Test AIModel model has the correct table name."""
    assert AIModel.__tablename__ == "aiModel"


def test_ai_model_columns():
    """Test AIModel model has the expected columns."""
    # Check primary key
    assert hasattr(AIModel, "id")

    # Check required columns
    assert hasattr(AIModel, "label")

    # Check optional columns
    assert hasattr(AIModel, "description")
    assert hasattr(AIModel, "created_at")

    # Check relationships
    assert hasattr(AIModel, "chat_sessions")
    assert hasattr(AIModel, "default_in_settings")


def test_ai_model_initialization(create_ai_model):
    """Test AIModel model initialization with valid data."""
    # Create with default values
    ai_model = create_ai_model()

    assert ai_model.label == "test_model"
    assert ai_model.description == "A test AI model"
    assert ai_model.created_at is None  # Will be set on commit

    # Create with custom values
    custom_model = create_ai_model(
        label="custom_model",
        description="Custom description",
    )

    assert custom_model.label == "custom_model"
    assert custom_model.description == "Custom description"


def test_ai_model_required_fields(db_session):
    """Test AIModel model required fields."""
    # Test missing label
    model_no_label = AIModel()
    db_session.add(model_no_label)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ai_model_unique_constraint(db_session, create_ai_model):
    """Test AIModel model label uniqueness constraint."""
    # Create and save first model
    model1 = create_ai_model(label="unique_test")
    db_session.add(model1)
    db_session.commit()

    # Try to create another model with the same label
    model2 = create_ai_model(label="unique_test")
    db_session.add(model2)

    # Should raise IntegrityError due to unique constraint on label
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ai_model_optional_fields(db_session):
    """Test AIModel model optional fields."""
    # Create model with minimal required fields
    model = AIModel(label="minimal")
    db_session.add(model)
    db_session.commit()

    # Verify optional fields
    assert model.description is None
    assert model.created_at is not None  # created_at has a default value


def test_ai_model_created_timestamp(db_session, create_ai_model):
    """Test AIModel created_at timestamp is set automatically."""
    # Create a model
    model = create_ai_model()

    # Before save, created_at should not be set
    assert model.created_at is None

    # Save the model
    db_session.add(model)
    db_session.commit()

    # After save, created_at should be set
    assert model.created_at is not None
    assert isinstance(model.created_at, datetime.datetime)


def test_ai_model_representation(create_ai_model):
    """Test AIModel model string representation."""
    ai_model = create_ai_model()

    # Test __repr__ method
    repr_string = repr(ai_model)
    assert "AIModel" in repr_string
    assert "test_model" in repr_string


def test_ai_model_relationships(
    db_session, create_ai_model, create_chat_session, create_character
):
    """Test AIModel model relationships with chat sessions."""
    # Create and save a model
    ai_model = create_ai_model()
    db_session.add(ai_model)
    db_session.commit()

    # Create characters with unique labels for each chat session
    character1 = create_character(label=f"char_for_ai_model_1_{ai_model.id}")
    character2 = create_character(label=f"char_for_ai_model_2_{ai_model.id}")
    db_session.add_all([character1, character2])
    db_session.commit()

    # Create chat sessions associated with the model and unique characters
    session1 = create_chat_session(ai_model=ai_model, character=character1)
    session2 = create_chat_session(ai_model=ai_model, character=character2)
    db_session.add_all([session1, session2])
    db_session.commit()

    # Test relationship fetching
    sessions = ai_model.chat_sessions.all()
    assert len(sessions) == 2

    # Verify bidirectional relationship
    for session in sessions:
        assert session.ai_model_id == ai_model.id
