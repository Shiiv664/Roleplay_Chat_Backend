"""Tests for the MessageRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.message import Message, MessageRole
from app.repositories.message_repository import MessageRepository
from app.utils.exceptions import DatabaseError


class TestMessageRepository:
    """Test message repository functionality."""

    @pytest.fixture
    def create_test_session(
        self,
        db_session,
        create_character,
        create_user_profile,
        create_ai_model,
        create_system_prompt,
        create_chat_session,
    ):
        """Create a test chat session for message tests."""
        import time

        timestamp = int(time.time())

        # Create entities with unique labels
        character = create_character(label=f"test_char_{timestamp}")
        user_profile = create_user_profile(label=f"test_profile_{timestamp}")
        ai_model = create_ai_model(label=f"test_model_{timestamp}")
        system_prompt = create_system_prompt(label=f"test_prompt_{timestamp}")

        db_session.add_all([character, user_profile, ai_model, system_prompt])
        db_session.flush()  # Get IDs

        # Create session
        session = create_chat_session(
            character=character,
            user_profile=user_profile,
            ai_model=ai_model,
            system_prompt=system_prompt,
        )

        db_session.add(session)
        db_session.commit()

        return session

    @pytest.fixture
    def create_test_messages(self, db_session, create_test_session, create_message):
        """Create sample messages for testing."""
        session = create_test_session
        messages = []

        # Create alternating user and assistant messages
        for i in range(10):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            content = f"Test message {i + 1} from {'user' if role == MessageRole.USER else 'assistant'}"
            message = create_message(
                chat_session=session,
                role=role,  # Pass the enum directly, not the value
                content=content,
            )
            messages.append(message)

        db_session.add_all(messages)
        db_session.commit()

        return messages, session

    def test_get_by_chat_session_id(self, db_session, create_test_messages):
        """Test retrieving messages for a chat session."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Get all messages
        retrieved_messages = repo.get_by_chat_session_id(session.id)

        # Verify messages were returned
        assert len(retrieved_messages) == 10
        # Messages should be sorted by timestamp (oldest first)
        for i in range(len(retrieved_messages) - 1):
            assert (
                retrieved_messages[i].timestamp <= retrieved_messages[i + 1].timestamp
            )

    def test_get_by_chat_session_id_with_pagination(
        self, db_session, create_test_messages
    ):
        """Test retrieving messages with pagination."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Test with limit
        limited_messages = repo.get_by_chat_session_id(session.id, limit=5)
        assert len(limited_messages) == 5

        # Test with offset
        offset_messages = repo.get_by_chat_session_id(session.id, offset=5)
        assert len(offset_messages) == 5

        # Test with both limit and offset
        paginated_messages = repo.get_by_chat_session_id(session.id, limit=3, offset=3)
        assert len(paginated_messages) == 3

        # Verify the messages are different between pages
        assert paginated_messages[0].id != limited_messages[0].id

    def test_get_paged_messages(self, db_session, create_test_messages):
        """Test getting paginated messages with metadata."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Get first page
        page1_messages, page1_meta = repo.get_paged_messages(
            session.id, page=1, page_size=5
        )

        # Verify metadata
        assert page1_meta["total_count"] == 10
        assert page1_meta["total_pages"] == 2
        assert page1_meta["current_page"] == 1
        assert page1_meta["page_size"] == 5
        assert page1_meta["has_next"] is True
        assert page1_meta["has_previous"] is False

        # Verify messages
        assert len(page1_messages) == 5

        # Get second page
        page2_messages, page2_meta = repo.get_paged_messages(
            session.id, page=2, page_size=5
        )

        # Verify metadata
        assert page2_meta["current_page"] == 2
        assert page2_meta["has_next"] is False
        assert page2_meta["has_previous"] is True

        # Verify messages
        assert len(page2_messages) == 5

        # Verify the messages are different between pages
        assert {m.id for m in page1_messages}.isdisjoint({m.id for m in page2_messages})

    def test_create_bulk(self, db_session, create_test_session):
        """Test creating multiple messages in bulk."""
        repo = MessageRepository(db_session)
        session = create_test_session

        # Prepare message data
        messages_data = [
            {
                "chat_session_id": session.id,
                "role": MessageRole.USER,
                "content": "User message 1",
            },
            {
                "chat_session_id": session.id,
                "role": MessageRole.ASSISTANT,
                "content": "Assistant response 1",
            },
            {
                "chat_session_id": session.id,
                "role": MessageRole.USER,
                "content": "User message 2",
            },
        ]

        # Create messages in bulk
        created_messages = repo.create_bulk(messages_data)
        db_session.commit()

        # Verify messages were created
        assert len(created_messages) == 3
        for i, message in enumerate(created_messages):
            assert message.id is not None
            assert message.chat_session_id == session.id
            assert message.content == messages_data[i]["content"]

    def test_get_latest_messages(self, db_session, create_test_messages):
        """Test getting the latest messages for a chat session."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Get latest 3 messages
        latest_messages = repo.get_latest_messages(session.id, count=3)

        # Verify the correct number of messages is returned
        assert len(latest_messages) == 3

        # Verify messages are in chronological order (oldest first)
        for i in range(len(latest_messages) - 1):
            assert latest_messages[i].timestamp <= latest_messages[i + 1].timestamp

        # Verify that the returned messages are among the created ones
        # (Not checking exact ordering because the timestamps might be the same in tests)
        latest_message_ids = {m.id for m in latest_messages}
        all_message_ids = {m.id for m in messages}
        assert latest_message_ids.issubset(all_message_ids)

    def test_delete_message_and_subsequent(self, db_session, create_test_messages):
        """Test deleting a message and all subsequent messages."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Verify we have 10 messages initially
        initial_count = repo.get_by_chat_session_id(session.id)
        assert len(initial_count) == 10

        # Get the 4th message (index 3) - this will be our target for deletion
        target_message = messages[3]

        # Delete the 4th message and all subsequent messages
        deleted_count = repo.delete_message_and_subsequent(target_message.id)
        db_session.commit()

        # Should have deleted 7 messages (4th through 10th)
        assert deleted_count == 7

        # Verify only first 3 messages remain
        remaining_messages = repo.get_by_chat_session_id(session.id)
        assert len(remaining_messages) == 3

        # Verify the remaining messages are the first 3
        remaining_ids = {m.id for m in remaining_messages}
        expected_ids = {messages[0].id, messages[1].id, messages[2].id}
        assert remaining_ids == expected_ids

    def test_delete_message_and_subsequent_last_message(
        self, db_session, create_test_messages
    ):
        """Test deleting the last message only."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Get the last message (index 9)
        last_message = messages[9]

        # Delete the last message
        deleted_count = repo.delete_message_and_subsequent(last_message.id)
        db_session.commit()

        # Should have deleted only 1 message
        assert deleted_count == 1

        # Verify 9 messages remain
        remaining_messages = repo.get_by_chat_session_id(session.id)
        assert len(remaining_messages) == 9

    def test_delete_message_and_subsequent_first_message(
        self, db_session, create_test_messages
    ):
        """Test deleting the first message and all subsequent messages."""
        repo = MessageRepository(db_session)
        messages, session = create_test_messages

        # Get the first message (index 0)
        first_message = messages[0]

        # Delete the first message and all subsequent
        deleted_count = repo.delete_message_and_subsequent(first_message.id)
        db_session.commit()

        # Should have deleted all 10 messages
        assert deleted_count == 10

        # Verify no messages remain
        remaining_messages = repo.get_by_chat_session_id(session.id)
        assert len(remaining_messages) == 0

    def test_database_error_handling(self, db_session, create_test_session):
        """Test handling of database errors in message repository methods."""
        repo = MessageRepository(db_session)
        session = create_test_session

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_by_chat_session_id(session.id)

            with pytest.raises(DatabaseError):
                repo.get_paged_messages(session.id)

            with pytest.raises(DatabaseError):
                repo.get_latest_messages(session.id)

        # Test create_bulk with error
        with patch.object(
            db_session, "add_all", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.create_bulk(
                    [
                        {
                            "chat_session_id": session.id,
                            "role": MessageRole.USER,
                            "content": "Test",
                        }
                    ]
                )
