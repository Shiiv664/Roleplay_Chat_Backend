"""Tests for the AIModel model using helper functions."""

import datetime

from sqlalchemy import Integer, String, Text, DateTime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ai_model import AIModel
from app.models.base import Base
from tests.models.helpers import (
    check_model_inheritance,
    check_model_tablename,
    check_model_columns_existence,
    check_model_repr,
    check_column_constraints,
    check_unique_constraint,
    check_relationship,
)


def test_ai_model_inheritance():
    """Test AIModel model inherits from correct base class."""
    check_model_inheritance(AIModel, Base)
    # AIModel doesn't use TimestampMixin but has its own created_at


def test_ai_model_tablename():
    """Test AIModel model has the correct table name."""
    check_model_tablename(AIModel, "aiModel")


def test_ai_model_columns():
    """Test AIModel model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "label",
        "description",
        "created_at",
        "chat_sessions",
        "default_in_settings",
    ]
    check_model_columns_existence(AIModel, expected_columns)
    
    # Test column constraints
    check_column_constraints(
        AIModel, "id", nullable=False, primary_key=True, column_type=Integer
    )
    
    check_column_constraints(
        AIModel, "label", nullable=False, unique=True, column_type=String
    )
    
    check_column_constraints(
        AIModel, "description", nullable=True, column_type=Text
    )
    
    # Check created_at with default
    check_column_constraints(
        AIModel, "created_at", nullable=False, column_type=DateTime
    )


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
    # Create a function that creates models with a specific label
    def create_model_with_label(label_value):
        return create_ai_model(label=label_value)
    
    # Test the unique constraint on the label field
    check_unique_constraint(
        db_session=db_session,
        model_class=AIModel,
        create_instance_with_unique=create_model_with_label,
        unique_field="label"
    )


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
    ai_model.id = 1  # Set ID manually for testing

    # Test representation using helper
    expected_attrs = {
        "id": 1,
        "label": "'test_model'"
    }
    
    check_model_repr(ai_model, expected_attrs)


def test_ai_model_relationships(
    db_session, create_ai_model, create_chat_session, create_character
):
    """Test AIModel model relationships with chat sessions."""
    # Create and save a model
    ai_model = create_ai_model()
    db_session.add(ai_model)
    db_session.commit()

    # Create a character for the chat session
    character = create_character(label=f"char_for_ai_model_{ai_model.id}")
    db_session.add(character)
    db_session.commit()

    # Create a chat session associated with the AI model
    session = create_chat_session(ai_model=ai_model, character=character)
    db_session.add(session)
    db_session.commit()

    # Test relationship using helper
    check_relationship(
        db_session=db_session,
        parent_obj=ai_model,
        child_obj=session,
        parent_attr="chat_sessions",
        child_attr="ai_model",
        is_collection=True,
        bidirectional=True
    )
    
    # Create a second session to verify multiple relationships
    character2 = create_character(label=f"char_for_ai_model_2_{ai_model.id}")
    db_session.add(character2)
    db_session.commit()
    
    session2 = create_chat_session(ai_model=ai_model, character=character2)
    db_session.add(session2)
    db_session.commit()
    
    # Verify multiple sessions
    sessions = ai_model.chat_sessions.all()
    assert len(sessions) == 2