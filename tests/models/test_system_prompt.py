"""Tests for the SystemPrompt model using helper functions."""

import datetime

import pytest
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.system_prompt import SystemPrompt
from tests.models.helpers import (
    check_column_constraints,
    check_model_columns_existence,
    check_model_inheritance,
    check_model_repr,
    check_model_tablename,
    check_relationship,
    check_unique_constraint,
)


def test_system_prompt_inheritance():
    """Test SystemPrompt model inherits from correct base class."""
    check_model_inheritance(SystemPrompt, Base)
    # SystemPrompt doesn't use TimestampMixin but has its own created_at


def test_system_prompt_tablename():
    """Test SystemPrompt model has the correct table name."""
    check_model_tablename(SystemPrompt, "systemPrompt")


def test_system_prompt_columns():
    """Test SystemPrompt model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "label",
        "content",
        "created_at",
        "chat_sessions",
        "default_in_settings",
    ]
    check_model_columns_existence(SystemPrompt, expected_columns)

    # Test column constraints
    check_column_constraints(
        SystemPrompt, "id", nullable=False, primary_key=True, column_type=Integer
    )

    check_column_constraints(
        SystemPrompt, "label", nullable=False, unique=True, column_type=String
    )

    check_column_constraints(SystemPrompt, "content", nullable=False, column_type=Text)

    # Check created_at with default
    check_column_constraints(
        SystemPrompt, "created_at", nullable=False, column_type=DateTime
    )


def test_system_prompt_initialization(create_system_prompt):
    """Test SystemPrompt model initialization with valid data."""
    # Create with default values
    system_prompt = create_system_prompt()

    assert system_prompt.label == "test_prompt"
    assert system_prompt.content == "This is a test system prompt content"
    assert system_prompt.created_at is None  # Will be set on commit

    # Create with custom values
    custom_prompt = create_system_prompt(
        label="custom_prompt",
        content="Custom system prompt content",
    )

    assert custom_prompt.label == "custom_prompt"
    assert custom_prompt.content == "Custom system prompt content"


def test_system_prompt_required_fields(db_session):
    """Test SystemPrompt model required fields."""
    # Test missing label
    prompt_no_label = SystemPrompt(content="Test content")
    db_session.add(prompt_no_label)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing content
    prompt_no_content = SystemPrompt(label="no_content_prompt")
    db_session.add(prompt_no_content)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_system_prompt_unique_constraint(db_session, create_system_prompt):
    """Test SystemPrompt model label uniqueness constraint."""

    # Create a function that creates prompts with a specific label
    def create_prompt_with_label(label_value):
        return create_system_prompt(label=label_value)

    # Test the unique constraint on the label field
    check_unique_constraint(
        db_session=db_session,
        model_class=SystemPrompt,
        create_instance_with_unique=create_prompt_with_label,
        unique_field="label",
    )


def test_system_prompt_created_timestamp(db_session, create_system_prompt):
    """Test SystemPrompt created_at timestamp is set automatically."""
    # Create a prompt
    prompt = create_system_prompt()

    # Before save, created_at should not be set
    assert prompt.created_at is None

    # Save the prompt
    db_session.add(prompt)
    db_session.commit()

    # After save, created_at should be set
    assert prompt.created_at is not None
    assert isinstance(prompt.created_at, datetime.datetime)


def test_system_prompt_representation(create_system_prompt):
    """Test SystemPrompt model string representation."""
    prompt = create_system_prompt()
    prompt.id = 1  # Set ID manually for testing

    # Test representation using helper
    expected_attrs = {"id": 1, "label": "'test_prompt'"}

    check_model_repr(prompt, expected_attrs)


def test_system_prompt_relationships(
    db_session, create_system_prompt, create_chat_session, create_character
):
    """Test SystemPrompt model relationships with chat sessions."""
    # Create and save a prompt
    prompt = create_system_prompt()
    db_session.add(prompt)
    db_session.commit()

    # Create a character for the chat session
    character = create_character(label=f"char_for_prompt_{prompt.id}")
    db_session.add(character)
    db_session.commit()

    # Create a chat session associated with the prompt
    session = create_chat_session(system_prompt=prompt, character=character)
    db_session.add(session)
    db_session.commit()

    # Test relationship using helper
    check_relationship(
        db_session=db_session,
        parent_obj=prompt,
        child_obj=session,
        parent_attr="chat_sessions",
        child_attr="system_prompt",
        is_collection=True,
        bidirectional=True,
    )

    # Create a second session to verify multiple relationships
    character2 = create_character(label=f"char_for_prompt_2_{prompt.id}")
    db_session.add(character2)
    db_session.commit()

    session2 = create_chat_session(system_prompt=prompt, character=character2)
    db_session.add(session2)
    db_session.commit()

    # Verify multiple sessions
    sessions = prompt.chat_sessions.all()
    assert len(sessions) == 2
