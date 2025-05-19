"""Tests for the SystemPrompt model."""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.system_prompt import SystemPrompt


def test_system_prompt_inheritance():
    """Test SystemPrompt model inherits from correct base class."""
    assert issubclass(SystemPrompt, Base)
    # SystemPrompt doesn't use TimestampMixin but has its own created_at


def test_system_prompt_tablename():
    """Test SystemPrompt model has the correct table name."""
    assert SystemPrompt.__tablename__ == "systemPrompt"


def test_system_prompt_columns():
    """Test SystemPrompt model has the expected columns."""
    # Check primary key
    assert hasattr(SystemPrompt, "id")

    # Check required columns
    assert hasattr(SystemPrompt, "label")
    assert hasattr(SystemPrompt, "content")

    # Check optional columns/fields
    assert hasattr(SystemPrompt, "created_at")

    # Check relationships
    assert hasattr(SystemPrompt, "chat_sessions")
    assert hasattr(SystemPrompt, "default_in_settings")


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
    # Create and save first prompt
    prompt1 = create_system_prompt(label="unique_test")
    db_session.add(prompt1)
    db_session.commit()

    # Try to create another prompt with the same label
    prompt2 = create_system_prompt(label="unique_test", content="Different content")
    db_session.add(prompt2)

    # Should raise IntegrityError due to unique constraint on label
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


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

    # Test __repr__ method
    repr_string = repr(prompt)
    assert "SystemPrompt" in repr_string
    assert "test_prompt" in repr_string


def test_system_prompt_relationships(
    db_session, create_system_prompt, create_chat_session, create_character
):
    """Test SystemPrompt model relationships with chat sessions."""
    # Create and save a prompt
    prompt = create_system_prompt()
    db_session.add(prompt)
    db_session.commit()

    # Create characters with unique labels for each chat session
    character1 = create_character(label=f"char_for_prompt_1_{prompt.id}")
    character2 = create_character(label=f"char_for_prompt_2_{prompt.id}")
    db_session.add_all([character1, character2])
    db_session.commit()

    # Create chat sessions associated with the prompt and unique characters
    session1 = create_chat_session(system_prompt=prompt, character=character1)
    session2 = create_chat_session(system_prompt=prompt, character=character2)
    db_session.add_all([session1, session2])
    db_session.commit()

    # Test relationship fetching
    sessions = prompt.chat_sessions.all()
    assert len(sessions) == 2

    # Verify bidirectional relationship
    for session in sessions:
        assert session.system_prompt_id == prompt.id
