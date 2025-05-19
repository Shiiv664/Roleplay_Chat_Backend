"""Tests for the Message model."""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.message import Message, MessageRole


def test_message_inheritance():
    """Test Message model inherits from correct base class."""
    assert issubclass(Message, Base)


def test_message_tablename():
    """Test Message model has the correct table name."""
    assert Message.__tablename__ == "message"


def test_message_columns():
    """Test Message model has the expected columns."""
    # Check primary key
    assert hasattr(Message, "id")

    # Check foreign key fields
    assert hasattr(Message, "chat_session_id")

    # Check content fields
    assert hasattr(Message, "role")
    assert hasattr(Message, "content")
    assert hasattr(Message, "timestamp")

    # Check relationships
    assert hasattr(Message, "chat_session")


def test_message_initialization(db_session, create_chat_session):
    """Test Message model initialization with valid data."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create message with minimal required fields
    message = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.USER,
        content="Hello, this is a test message!",
    )

    # Verify field values
    assert message.chat_session_id == chat_session.id
    assert message.role == MessageRole.USER
    assert message.content == "Hello, this is a test message!"
    assert message.timestamp is None  # Should be None before saving

    # Add to session and verify timestamp
    db_session.add(message)
    db_session.commit()

    assert message.id is not None
    assert message.timestamp is not None
    assert isinstance(message.timestamp, datetime.datetime)

    # Create message with assistant role
    message_assistant = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Hello, I'm an AI assistant!",
    )

    # Verify field values
    assert message_assistant.role == MessageRole.ASSISTANT
    assert message_assistant.content == "Hello, I'm an AI assistant!"


def test_message_required_fields(db_session, create_chat_session):
    """Test Message model required fields."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Test missing chat_session_id
    message_no_session = Message(
        role=MessageRole.USER, content="Test message without session"
    )
    db_session.add(message_no_session)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing role
    message_no_role = Message(
        chat_session_id=chat_session.id, content="Test message without role"
    )
    db_session.add(message_no_role)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Test missing content
    message_no_content = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.USER,
    )
    db_session.add(message_no_content)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_message_foreign_key_constraints(db_session, create_chat_session):
    """Test Message model foreign key constraints."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Test invalid foreign key for chat_session_id
    invalid_session_id = 999999  # Non-existent ID
    message_invalid_session = Message(
        chat_session_id=invalid_session_id,
        role=MessageRole.USER,
        content="Test message with invalid session ID",
    )
    db_session.add(message_invalid_session)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_message_role_enum_values(db_session, create_chat_session):
    """Test Message model role enum values."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create messages with valid roles
    message_user = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="User message"
    )
    message_assistant = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Assistant message",
    )

    # Add to session and commit
    db_session.add_all([message_user, message_assistant])
    db_session.commit()

    # Verify roles are stored correctly
    assert message_user.role == MessageRole.USER
    assert message_user.role.value == "user"
    assert message_assistant.role == MessageRole.ASSISTANT
    assert message_assistant.role.value == "assistant"


def test_message_relationship(db_session, create_chat_session):
    """Test Message model relationship with ChatSession."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create message
    message = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.USER,
        content="Test relationship message",
    )
    db_session.add(message)
    db_session.commit()

    # Test relationship with chat_session
    assert message.chat_session_id == chat_session.id
    assert message.chat_session == chat_session

    # Test bidirectional relationship
    assert message in chat_session.messages


def test_message_multiple_per_session(db_session, create_chat_session):
    """Test multiple messages can be added to a session."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create multiple messages
    message1 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="First message"
    )
    message2 = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Second message",
    )
    message3 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Third message"
    )

    db_session.add_all([message1, message2, message3])
    db_session.commit()

    # Test multiple messages are associated with the session
    messages = chat_session.messages.all()
    assert len(messages) == 3

    # Check message contents
    message_contents = [m.content for m in messages]
    assert "First message" in message_contents
    assert "Second message" in message_contents
    assert "Third message" in message_contents


def test_message_cascade_delete_with_chat_session(db_session, create_chat_session):
    """Test messages are deleted when the chat session is deleted."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create messages
    message1 = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="First message"
    )
    message2 = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="Second message",
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


def test_message_representation(db_session, create_chat_session):
    """Test Message model string representation."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()

    # Create message
    message = Message(
        chat_session_id=chat_session.id,
        role=MessageRole.USER,
        content="Test repr message",
    )
    db_session.add(message)
    db_session.commit()

    # Test __repr__ method
    repr_string = repr(message)
    assert "Message" in repr_string
    assert f"id={message.id}" in repr_string
    assert f"chat_session_id={chat_session.id}" in repr_string
    assert "user" in repr_string  # Check that role.value is included
