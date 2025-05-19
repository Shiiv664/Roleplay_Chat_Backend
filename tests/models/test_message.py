"""Tests for the Message model using helper functions."""

import datetime

from sqlalchemy import Integer, Text, DateTime, Enum

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.message import Message, MessageRole
from tests.models.helpers import (
    check_model_inheritance,
    check_model_tablename,
    check_model_columns_existence,
    check_model_repr,
    check_column_constraints,
    check_cascade_delete,
    check_relationship,
    check_foreign_key_constraint,
    check_enum_values,
    check_enum_field,
)


def test_message_inheritance():
    """Test Message model inherits from correct base class."""
    check_model_inheritance(Message, Base)


def test_message_tablename():
    """Test Message model has the correct table name."""
    check_model_tablename(Message, "message")


def test_message_columns():
    """Test Message model has the expected columns."""
    # Test column existence
    expected_columns = [
        "id",
        "chat_session_id",
        "role",
        "content",
        "timestamp",
        "chat_session",
    ]
    check_model_columns_existence(Message, expected_columns)
    
    # Test column constraints
    check_column_constraints(
        Message, "id", nullable=False, primary_key=True, column_type=Integer
    )
    
    check_column_constraints(
        Message, "chat_session_id", nullable=False, column_type=Integer
    )
    
    check_column_constraints(
        Message, "role", nullable=False, column_type=Enum
    )
    
    check_column_constraints(
        Message, "content", nullable=False, column_type=Text
    )
    
    check_column_constraints(
        Message, "timestamp", nullable=False, column_type=DateTime
    )


def test_message_role_enum():
    """Test MessageRole enum has expected values."""
    # Test the enum values
    expected_values = {
        "USER": "user",
        "ASSISTANT": "assistant",
    }
    check_enum_values(MessageRole, expected_values)


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
    
    # Create a valid Message factory function
    def create_valid_message(**kwargs):
        valid_fields = {
            "chat_session_id": chat_session.id,
            "role": MessageRole.USER,
            "content": "Test message",
        }
        valid_fields.update(kwargs)
        return Message(**valid_fields)
    
    # Test chat_session_id foreign key constraint
    check_foreign_key_constraint(
        db_session=db_session,
        model_factory=create_valid_message,
        fk_field="chat_session_id",
        invalid_id=999999
    )


def test_message_role_enum_values(db_session, create_chat_session):
    """Test Message model role enum values."""
    # Create chat session
    chat_session = create_chat_session()
    db_session.add(chat_session)
    db_session.commit()
    
    # Create a message creation function for the enum test
    def create_message_with_role(role):
        return Message(
            chat_session_id=chat_session.id,
            role=role,
            content=f"Message with role {role.value}"
        )
    
    # Test all enum values
    check_enum_field(
        db_session=db_session,
        model_class=Message,
        field_name="role",
        enum_class=MessageRole,
        create_instance=create_message_with_role
    )


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

    # Test relationship using helper
    check_relationship(
        db_session=db_session,
        parent_obj=chat_session,
        child_obj=message,
        parent_attr="messages",
        child_attr="chat_session",
        is_collection=True,
        bidirectional=True
    )


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

    # Create message
    message = Message(
        chat_session_id=chat_session.id, role=MessageRole.USER, content="Test cascade delete"
    )
    db_session.add(message)
    db_session.commit()

    # Test cascade delete using helper
    check_cascade_delete(
        db_session=db_session,
        parent_obj=chat_session,
        child_obj=message,
        parent_attr="messages",
        child_attr="chat_session",
        child_class=Message
    )


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

    # Test representation using helper
    expected_attrs = {
        "id": message.id,
        "chat_session_id": chat_session.id,
        "role": "user"  # The enum's value
    }
    
    check_model_repr(message, expected_attrs)