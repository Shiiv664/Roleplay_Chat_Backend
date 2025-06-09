"""Integration tests for the Messages API with real database operations.

These tests verify that database transactions actually work correctly,
without mocking the service layer. They would have caught the transaction
management bug that unit tests missed.

These tests create their own isolated data and use a separate database
to ensure complete isolation from other tests.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.ai_model import AIModel
from app.models.base import Base
from app.models.character import Character
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile


@pytest.fixture(scope="class")
def integration_db_engine():
    """Create a separate SQLite database for integration tests."""
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    db_path = f"sqlite:///{temp_db.name}"

    # Create engine with foreign key support
    engine = create_engine(
        db_path,
        connect_args={"check_same_thread": False},
    )

    # Enable foreign key constraints
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()
    Path(temp_db.name).unlink(missing_ok=True)


@pytest.fixture
def integration_db_session(integration_db_engine):
    """Create a fresh database session for each integration test."""
    SessionFactory = sessionmaker(bind=integration_db_engine)
    session = SessionFactory()

    yield session

    # Clean up the session
    session.rollback()
    # Clear all data from all tables
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture
def integration_test_data(integration_db_session):
    """Create a complete set of test data for integration tests."""
    # Create character
    character = Character(
        label="integration_test_char",
        name="Integration Test Character",
        description="A character for integration testing",
    )
    integration_db_session.add(character)

    # Create user profile
    user_profile = UserProfile(
        label="integration_test_user",
        name="Integration Test User",
        description="A user profile for integration testing",
    )
    integration_db_session.add(user_profile)

    # Create AI model
    ai_model = AIModel(
        label="integration_test_model",
        description="An AI model for integration testing",
    )
    integration_db_session.add(ai_model)

    # Create system prompt
    system_prompt = SystemPrompt(
        label="integration_test_prompt",
        content="You are a helpful assistant for integration testing.",
    )
    integration_db_session.add(system_prompt)

    # Flush to get IDs
    integration_db_session.flush()

    # Create chat session
    chat_session = ChatSession(
        character_id=character.id,
        user_profile_id=user_profile.id,
        ai_model_id=ai_model.id,
        system_prompt_id=system_prompt.id,
    )
    integration_db_session.add(chat_session)
    integration_db_session.commit()

    return {
        "character": character,
        "user_profile": user_profile,
        "ai_model": ai_model,
        "system_prompt": system_prompt,
        "chat_session": chat_session,
    }


@pytest.fixture
def integration_app_with_db(integration_db_engine):
    """Create a Flask app configured to use the integration test database."""
    from pathlib import Path

    from flask import Flask, request

    from app.api import api_bp
    from app.config import TestingConfig

    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    app.config["SERVER_NAME"] = "localhost.localdomain"

    # Override the database configuration to use our integration test database
    app.config["DATABASE_URL"] = str(integration_db_engine.url)

    # Patch the database session to use our integration database
    from unittest.mock import patch

    def get_integration_session():
        SessionFactory = sessionmaker(bind=integration_db_engine)
        return SessionFactory()

    with patch("app.utils.db.get_session", side_effect=get_integration_session):
        with patch("app.utils.db.get_db_session") as mock_get_db_session:

            def mock_session_context():
                session = get_integration_session()

                class SessionContext:
                    def __enter__(self):
                        return session

                    def __exit__(self, exc_type, exc_val, exc_tb):
                        if exc_type is not None:
                            session.rollback()
                        else:
                            session.commit()
                        session.close()

                return SessionContext()

            mock_get_db_session.side_effect = mock_session_context

            # Configure uploads directory for testing
            UPLOAD_FOLDER = Path("test_uploads_integration")
            UPLOAD_FOLDER.mkdir(exist_ok=True)

            @app.route("/uploads/<path:filename>")
            def serve_uploads(filename):
                from flask import send_from_directory

                try:
                    return send_from_directory(str(UPLOAD_FOLDER), filename)
                except FileNotFoundError:
                    return "File not found", 404
                except Exception as e:
                    app.logger.error(f"Error serving uploaded file {filename}: {e}")
                    return "Internal server error", 500

            # Add is_debug property to request context
            @app.before_request
            def before_request():
                request.is_debug = app.debug

            # Register the API blueprint
            app.register_blueprint(api_bp)

            yield app

            # Cleanup uploads directory
            import shutil

            if UPLOAD_FOLDER.exists():
                shutil.rmtree(UPLOAD_FOLDER)


@pytest.fixture
def integration_client(integration_app_with_db):
    """Create a test client for integration tests."""
    with integration_app_with_db.test_client() as client:
        with integration_app_with_db.app_context():
            yield client


class TestMessagesAPIIntegration:
    """Integration tests for Messages API with real database operations."""

    def test_delete_message_actually_removes_from_database(
        self, integration_client, integration_db_session, integration_test_data
    ):
        """Test that DELETE actually removes messages from database.

        This integration test verifies that the delete operation commits
        the transaction and the messages are actually gone from the database.
        """
        chat_session = integration_test_data["chat_session"]

        # Create real messages in the database
        messages = []
        for i in range(5):
            message = Message(
                chat_session_id=chat_session.id,
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Test message {i+1}",
                timestamp=datetime.now(),
            )
            messages.append(message)
            integration_db_session.add(message)

        integration_db_session.commit()

        # Verify messages exist in database before deletion
        initial_count = (
            integration_db_session.query(Message)
            .filter_by(chat_session_id=chat_session.id)
            .count()
        )
        assert initial_count == 5

        # Get the ID of the middle message (should delete this and subsequent ones)
        target_message_id = messages[2].id  # 3rd message

        # Make DELETE request without mocking the service
        response = integration_client.delete(f"/api/v1/messages/{target_message_id}")

        # Verify API response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["deleted_count"] == 3  # Should delete messages 3, 4, 5

        # CRITICAL: Verify messages are actually gone from database
        remaining_count = (
            integration_db_session.query(Message)
            .filter_by(chat_session_id=chat_session.id)
            .count()
        )
        assert remaining_count == 2, "Messages should actually be deleted from database"

        # Verify only the first 2 messages remain
        remaining_messages = (
            integration_db_session.query(Message)
            .filter_by(chat_session_id=chat_session.id)
            .order_by(Message.id)
            .all()
        )

        assert len(remaining_messages) == 2
        assert remaining_messages[0].content == "Test message 1"
        assert remaining_messages[1].content == "Test message 2"

        # Verify the deleted messages are actually gone
        deleted_message = (
            integration_db_session.query(Message)
            .filter_by(id=target_message_id)
            .first()
        )
        assert (
            deleted_message is None
        ), "Target message should be completely gone from database"

    def test_delete_nonexistent_message_no_side_effects(
        self, integration_client, integration_db_session, integration_test_data
    ):
        """Test that deleting non-existent message doesn't affect other data."""
        chat_session = integration_test_data["chat_session"]

        # Create some real messages
        message = Message(
            chat_session_id=chat_session.id,
            role=MessageRole.USER,
            content="Should not be affected",
            timestamp=datetime.now(),
        )
        integration_db_session.add(message)
        integration_db_session.commit()

        initial_count = integration_db_session.query(Message).count()

        # Try to delete non-existent message
        response = integration_client.delete("/api/v1/messages/99999")

        # Should return 404
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

        # Verify no messages were affected
        final_count = integration_db_session.query(Message).count()
        assert final_count == initial_count

        # Verify the original message is still there
        remaining_message = (
            integration_db_session.query(Message).filter_by(id=message.id).first()
        )
        assert remaining_message is not None
        assert remaining_message.content == "Should not be affected"

    def test_update_message_actually_persists_changes(
        self,
        integration_client,
        integration_db_session,
        integration_test_data,
        integration_db_engine,
    ):
        """Test that PUT actually updates the message in the database."""
        chat_session = integration_test_data["chat_session"]

        # Create a real message
        original_content = "Original content"
        message = Message(
            chat_session_id=chat_session.id,
            role=MessageRole.USER,
            content=original_content,
            timestamp=datetime.now(),
        )
        integration_db_session.add(message)
        integration_db_session.commit()
        message_id = message.id

        # Close the test session to ensure no interference
        integration_db_session.close()

        # Update the message via API
        new_content = "Updated content"
        response = integration_client.put(
            f"/api/v1/messages/{message_id}",
            data=json.dumps({"content": new_content}),
            content_type="application/json",
        )

        # Verify API response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["content"] == new_content

        # CRITICAL: Verify the change is actually persisted in database
        # Create a completely fresh session to verify persistence
        from sqlalchemy.orm import sessionmaker

        SessionFactory = sessionmaker(bind=integration_db_engine)
        verify_session = SessionFactory()
        try:
            updated_message = (
                verify_session.query(Message).filter_by(id=message_id).first()
            )
            assert (
                updated_message.content == new_content
            ), "Update should be committed to database"
            assert updated_message.content != original_content
        finally:
            verify_session.close()

    def test_delete_transaction_rollback_on_error(
        self, integration_client, integration_db_session, integration_test_data
    ):
        """Test that if delete fails, no partial changes are committed.

        This test would catch transaction management issues where some
        changes might be committed even if the operation fails.
        """
        chat_session = integration_test_data["chat_session"]

        # Create messages
        messages = []
        for i in range(3):
            message = Message(
                chat_session_id=chat_session.id,
                role=MessageRole.USER,
                content=f"Message {i+1}",
                timestamp=datetime.now(),
            )
            messages.append(message)
            integration_db_session.add(message)

        integration_db_session.commit()
        initial_count = integration_db_session.query(Message).count()

        # Try to delete a message that doesn't exist
        response = integration_client.delete("/api/v1/messages/99999")
        assert response.status_code == 404

        # Verify no messages were affected (transaction rollback)
        final_count = integration_db_session.query(Message).count()
        assert final_count == initial_count, "Failed delete should not affect any data"

        # Verify all original messages still exist
        for original_message in messages:
            existing_message = (
                integration_db_session.query(Message)
                .filter_by(id=original_message.id)
                .first()
            )
            assert (
                existing_message is not None
            ), f"Message {original_message.id} should still exist"

    def test_concurrent_operations_transaction_isolation(
        self, integration_client, integration_db_session, integration_test_data
    ):
        """Test that database operations are properly isolated."""
        chat_session = integration_test_data["chat_session"]

        # Create a test message
        message = Message(
            chat_session_id=chat_session.id,
            role=MessageRole.USER,
            content="Test isolation",
            timestamp=datetime.now(),
        )
        integration_db_session.add(message)
        integration_db_session.commit()

        # Verify message exists
        assert (
            integration_db_session.query(Message).filter_by(id=message.id).first()
            is not None
        )

        # Delete via API
        response = integration_client.delete(f"/api/v1/messages/{message.id}")
        assert response.status_code == 200

        # Verify message is actually gone from database
        deleted_message = (
            integration_db_session.query(Message).filter_by(id=message.id).first()
        )
        assert deleted_message is None, "Message should be completely removed"

    def test_message_cascade_delete_integrity(
        self,
        integration_client,
        integration_db_session,
        integration_test_data,
        integration_db_engine,
    ):
        """Test that cascade delete maintains conversation integrity."""
        chat_session = integration_test_data["chat_session"]
        chat_session_id = chat_session.id

        # Create a conversation with alternating user/assistant messages
        message_ids = []
        for i in range(6):
            message = Message(
                chat_session_id=chat_session_id,
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i+1}",
                timestamp=datetime.now(),
            )
            integration_db_session.add(message)
            integration_db_session.flush()  # Get the ID
            message_ids.append(message.id)

        integration_db_session.commit()

        # Delete the 4th message (index 3) - should delete messages 4, 5, 6
        target_message_id = message_ids[3]

        # Close the test session to avoid interference
        integration_db_session.close()

        response = integration_client.delete(f"/api/v1/messages/{target_message_id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["data"]["deleted_count"] == 3

        # Verify conversation integrity using a fresh session
        from sqlalchemy.orm import sessionmaker

        SessionFactory = sessionmaker(bind=integration_db_engine)
        verify_session = SessionFactory()
        try:
            remaining_messages = (
                verify_session.query(Message)
                .filter_by(chat_session_id=chat_session_id)
                .order_by(Message.id)
                .all()
            )

            assert len(remaining_messages) == 3
            for i, msg in enumerate(remaining_messages):
                assert msg.content == f"Message {i+1}"

            # Verify deleted messages are completely gone
            for i in range(3, 6):
                deleted_msg = (
                    verify_session.query(Message).filter_by(id=message_ids[i]).first()
                )
                assert deleted_msg is None, f"Message {i+1} should be deleted"
        finally:
            verify_session.close()
