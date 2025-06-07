"""Tests for the ChatSession model using helper functions."""

import datetime

import pytest
from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from tests.models.helpers import (
    check_cascade_delete,
    check_column_constraints,
    check_foreign_key_constraint,
    check_model_columns_existence,
    check_model_inheritance,
    check_model_repr,
    check_model_tablename,
    check_relationship,
)


def test_chat_session_inheritance():
    """Test ChatSession model inherits from correct base class."""
    check_model_inheritance(ChatSession, Base)


def test_chat_session_tablename():
    """Test ChatSession model has the correct table name."""
    check_model_tablename(ChatSession, "chatSession")


def test_chat_session_columns():
    """Test ChatSession model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "start_time",
        "updated_at",
        "character_id",
        "user_profile_id",
        "ai_model_id",
        "system_prompt_id",
        "pre_prompt",
        "pre_prompt_enabled",
        "post_prompt",
        "post_prompt_enabled",
        "formatting_settings",
        "first_message_initialized",
        "character",
        "user_profile",
        "ai_model",
        "system_prompt",
        "messages",
    ]
    check_model_columns_existence(ChatSession, expected_columns)

    # Test primary key and timestamp columns
    check_column_constraints(
        ChatSession, "id", nullable=False, primary_key=True, column_type=Integer
    )

    check_column_constraints(
        ChatSession, "start_time", nullable=False, column_type=DateTime
    )

    check_column_constraints(
        ChatSession, "updated_at", nullable=False, column_type=DateTime
    )

    # Test foreign key columns
    check_column_constraints(
        ChatSession, "character_id", nullable=False, column_type=Integer
    )

    check_column_constraints(
        ChatSession, "user_profile_id", nullable=False, column_type=Integer
    )

    check_column_constraints(
        ChatSession, "ai_model_id", nullable=False, column_type=Integer
    )

    check_column_constraints(
        ChatSession, "system_prompt_id", nullable=False, column_type=Integer
    )

    # Test optional fields
    check_column_constraints(ChatSession, "pre_prompt", nullable=True, column_type=Text)

    check_column_constraints(
        ChatSession, "pre_prompt_enabled", nullable=False, column_type=Boolean
    )

    check_column_constraints(
        ChatSession, "post_prompt", nullable=True, column_type=Text
    )

    check_column_constraints(
        ChatSession, "post_prompt_enabled", nullable=False, column_type=Boolean
    )

    # Test formatting settings field
    check_column_constraints(
        ChatSession, "formatting_settings", nullable=True, column_type=Text
    )

    # Test first message initialized field
    check_column_constraints(
        ChatSession, "first_message_initialized", nullable=False, column_type=Boolean
    )


def test_chat_session_initialization(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
):
    """Test ChatSession model initialization with valid data."""
    # Create parent entities
    character = create_character(label="chat_session_test_char")
    user_profile = create_user_profile(label="chat_session_test_profile")
    ai_model = create_ai_model(label="chat_session_test_model")
    system_prompt = create_system_prompt(label="chat_session_test_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session with minimal required fields
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )

    # Verify field values
    assert chat_session.character_id == character.id
    assert chat_session.user_profile_id == user_profile.id
    assert chat_session.ai_model_id == ai_model.id
    assert chat_session.system_prompt_id == system_prompt.id

    # Default values for optional fields should be None before saving
    assert chat_session.pre_prompt is None
    # Note: Boolean defaults are not applied until the session is saved
    assert chat_session.post_prompt is None

    # Add to session and verify timestamps
    db_session.add(chat_session)
    db_session.commit()

    assert chat_session.id is not None
    assert chat_session.start_time is not None
    assert chat_session.updated_at is not None
    assert isinstance(chat_session.start_time, datetime.datetime)
    assert isinstance(chat_session.updated_at, datetime.datetime)

    # After saving, default values should be applied
    assert chat_session.pre_prompt_enabled is False
    assert chat_session.post_prompt_enabled is False

    # Create chat session with all fields
    chat_session_full = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
        pre_prompt="Custom pre prompt",
        pre_prompt_enabled=True,
        post_prompt="Custom post prompt",
        post_prompt_enabled=True,
    )

    # Verify field values
    assert chat_session_full.pre_prompt == "Custom pre prompt"
    assert chat_session_full.pre_prompt_enabled is True
    assert chat_session_full.post_prompt == "Custom post prompt"
    assert chat_session_full.post_prompt_enabled is True


def test_chat_session_required_fields(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
):
    """Test ChatSession model required fields."""
    # Create parent entities
    character = create_character(label="required_fields_char")
    user_profile = create_user_profile(label="required_fields_profile")
    ai_model = create_ai_model(label="required_fields_model")
    system_prompt = create_system_prompt(label="required_fields_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Test missing character_id
    session_no_character = ChatSession(
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(session_no_character)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing user_profile_id
    session_no_user = ChatSession(
        character_id=character.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(session_no_user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing ai_model_id
    session_no_model = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(session_no_model)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing system_prompt_id
    session_no_prompt = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
    )
    db_session.add(session_no_prompt)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_chat_session_foreign_key_constraints(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
):
    """Test ChatSession model foreign key constraints."""
    # Create parent entities
    character = create_character(label="fk_test_char")
    user_profile = create_user_profile(label="fk_test_profile")
    ai_model = create_ai_model(label="fk_test_model")
    system_prompt = create_system_prompt(label="fk_test_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create a valid ChatSession factory function for the test
    def create_valid_session(**kwargs):
        valid_fields = {
            "character_id": character.id,
            "user_profile_id": user_profile.id,
            "ai_model_id": ai_model.id,
            "system_prompt_id": system_prompt.id,
        }
        valid_fields.update(kwargs)
        return ChatSession(**valid_fields)

    # Test character_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_session,
        fk_field="character_id",
        invalid_id=999999,
    )

    # Test user_profile_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_session,
        fk_field="user_profile_id",
        invalid_id=999999,
    )

    # Test ai_model_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_session,
        fk_field="ai_model_id",
        invalid_id=999999,
    )

    # Test system_prompt_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_session,
        fk_field="system_prompt_id",
        invalid_id=999999,
    )


def test_chat_session_relationships(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
    create_chat_session,
):
    """Test ChatSession model relationships."""
    # Create parent entities
    character = create_character(label="rel_test_char")
    user_profile = create_user_profile(label="rel_test_profile")
    ai_model = create_ai_model(label="rel_test_model")
    system_prompt = create_system_prompt(label="rel_test_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session
    chat_session = create_chat_session(
        character=character,
        user_profile=user_profile,
        ai_model=ai_model,
        system_prompt=system_prompt,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Test relationship with character
    assert chat_session.character.id == character.id
    assert chat_session.character.label == character.label

    # Test relationship with user_profile
    assert chat_session.user_profile.id == user_profile.id
    assert chat_session.user_profile.label == user_profile.label

    # Test relationship with ai_model
    assert chat_session.ai_model.id == ai_model.id
    assert chat_session.ai_model.label == ai_model.label

    # Test relationship with system_prompt
    assert chat_session.system_prompt.id == system_prompt.id
    assert chat_session.system_prompt.label == system_prompt.label

    # Test bidirectional relationships
    assert chat_session in character.chat_sessions
    assert chat_session in user_profile.chat_sessions
    assert chat_session in ai_model.chat_sessions
    assert chat_session in system_prompt.chat_sessions


def test_chat_session_message_relationship(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
    create_chat_session,
):
    """Test ChatSession relationship with messages."""
    # Create parent entities
    character = create_character(label="msg_rel_char")
    user_profile = create_user_profile(label="msg_rel_profile")
    ai_model = create_ai_model(label="msg_rel_model")
    system_prompt = create_system_prompt(label="msg_rel_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session
    chat_session = create_chat_session(
        character=character,
        user_profile=user_profile,
        ai_model=ai_model,
        system_prompt=system_prompt,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Create messages for this chat session
    message1 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Hello there!"
    )
    db_session.add(message1)
    db_session.commit()

    # Test relationship with first message
    check_relationship(
        db_session=db_session,
        parent_obj=chat_session,
        child_obj=message1,
        parent_attr="messages",
        child_attr="chat_session",
        is_collection=True,
        bidirectional=True,
    )

    # Create another message
    message2 = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Hi! How can I help you today?",
    )
    db_session.add(message2)
    db_session.commit()

    # Test relationship with messages
    messages = chat_session.messages.all()
    assert len(messages) == 2

    # Check the messages are correct
    message_contents = [m.content for m in messages]
    assert "Hello there!" in message_contents
    assert "Hi! How can I help you today?" in message_contents

    # Check the roles are correct
    message_roles = [m.role for m in messages]
    assert MessageRole.USER in message_roles
    assert MessageRole.ASSISTANT in message_roles


def test_chat_session_cascade_delete(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
    create_chat_session,
):
    """Test ChatSession cascade delete behavior with messages."""
    # Create parent entities
    character = create_character(label="cascade_char")
    user_profile = create_user_profile(label="cascade_profile")
    ai_model = create_ai_model(label="cascade_model")
    system_prompt = create_system_prompt(label="cascade_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session
    chat_session = create_chat_session(
        character=character,
        user_profile=user_profile,
        ai_model=ai_model,
        system_prompt=system_prompt,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Create messages for this chat session
    message = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Test message"
    )
    db_session.add(message)
    db_session.commit()

    # Test cascade delete with helper
    check_cascade_delete(
        db_session=db_session,
        parent_obj=chat_session,
        child_obj=message,
        parent_attr="messages",
        child_attr="chat_session",
        child_class=Message,
    )


def test_chat_session_cascade_delete_with_character(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
    create_chat_session,
):
    """Test ChatSession cascade delete when character is deleted."""
    # Create parent entities
    character = create_character(label="cascade_parent_char")
    user_profile = create_user_profile(label="cascade_parent_profile")
    ai_model = create_ai_model(label="cascade_parent_model")
    system_prompt = create_system_prompt(label="cascade_parent_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session
    chat_session = create_chat_session(
        character=character,
        user_profile=user_profile,
        ai_model=ai_model,
        system_prompt=system_prompt,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Test cascade delete from character to chat session
    check_cascade_delete(
        db_session=db_session,
        parent_obj=character,
        child_obj=chat_session,
        parent_attr="chat_sessions",
        child_attr="character",
        child_class=ChatSession,
    )


def test_chat_session_representation(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
    create_chat_session,
):
    """Test ChatSession model string representation."""
    # Create parent entities
    character = create_character(label="repr_test_char")
    user_profile = create_user_profile(label="repr_test_profile")
    ai_model = create_ai_model(label="repr_test_model")
    system_prompt = create_system_prompt(label="repr_test_prompt")

    db_session.add_all([character, user_profile, ai_model, system_prompt])
    db_session.commit()

    # Create chat session
    chat_session = create_chat_session(
        character=character,
        user_profile=user_profile,
        ai_model=ai_model,
        system_prompt=system_prompt,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Test representation using helper
    expected_attrs = {
        "id": chat_session.id,
        "character_id": character.id,
        "user_profile_id": user_profile.id,
    }

    check_model_repr(chat_session, expected_attrs)
