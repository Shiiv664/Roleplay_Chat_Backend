"""Tests for the ChatSession model."""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole


def test_chat_session_inheritance():
    """Test ChatSession model inherits from correct base class."""
    assert issubclass(ChatSession, Base)


def test_chat_session_tablename():
    """Test ChatSession model has the correct table name."""
    assert ChatSession.__tablename__ == "chatSession"


def test_chat_session_columns():
    """Test ChatSession model has the expected columns."""
    # Check primary key
    assert hasattr(ChatSession, "id")

    # Check timestamp fields
    assert hasattr(ChatSession, "start_time")
    assert hasattr(ChatSession, "updated_at")

    # Check foreign key fields
    assert hasattr(ChatSession, "character_id")
    assert hasattr(ChatSession, "user_profile_id")
    assert hasattr(ChatSession, "ai_model_id")
    assert hasattr(ChatSession, "system_prompt_id")

    # Check optional fields
    assert hasattr(ChatSession, "pre_prompt")
    assert hasattr(ChatSession, "pre_prompt_enabled")
    assert hasattr(ChatSession, "post_prompt")
    assert hasattr(ChatSession, "post_prompt_enabled")

    # Check relationships
    assert hasattr(ChatSession, "character")
    assert hasattr(ChatSession, "user_profile")
    assert hasattr(ChatSession, "ai_model")
    assert hasattr(ChatSession, "system_prompt")
    assert hasattr(ChatSession, "messages")


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

    # Test invalid foreign key for character_id
    invalid_character_id = 999999  # Non-existent ID
    session_invalid_char = ChatSession(
        character_id=invalid_character_id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(session_invalid_char)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test invalid foreign key for user_profile_id
    invalid_profile_id = 999999  # Non-existent ID
    session_invalid_profile = ChatSession(
        character_id=character.id,
        user_profile_id=invalid_profile_id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(session_invalid_profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_chat_session_relationships(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
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
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
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
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Create messages for this chat session
    message1 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Hello there!"
    )
    message2 = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Hi! How can I help you today?",
    )
    db_session.add_all([message1, message2])
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

    # Test bidirectional relationship
    for message in messages:
        assert message.chat_session_id == chat_session.id
        assert message.chat_session == chat_session


def test_chat_session_cascade_delete(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
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
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Create messages for this chat session
    message1 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Test message 1"
    )
    message2 = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Test message 2",
    )
    db_session.add_all([message1, message2])
    db_session.commit()

    # Store message IDs for verification
    message_ids = [message1.id, message2.id]

    # Delete the chat session
    db_session.delete(chat_session)
    db_session.commit()

    # Verify messages were deleted (cascade delete)
    for message_id in message_ids:
        deleted_message = db_session.query(Message).filter_by(id=message_id).first()
        assert deleted_message is None


def test_chat_session_cascade_delete_with_character(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
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
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Store chat session ID for verification
    chat_session_id = chat_session.id

    # Delete the character (should cascade delete the chat session)
    db_session.delete(character)
    db_session.commit()

    # Verify chat session was deleted (cascade delete)
    deleted_session = (
        db_session.query(ChatSession).filter_by(id=chat_session_id).first()
    )
    assert deleted_session is None


def test_chat_session_representation(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
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
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    db_session.add(chat_session)
    db_session.commit()

    # Test __repr__ method
    repr_string = repr(chat_session)
    assert "ChatSession" in repr_string
    assert f"id={chat_session.id}" in repr_string
    assert f"character_id={character.id}" in repr_string
    assert f"user_profile_id={user_profile.id}" in repr_string
