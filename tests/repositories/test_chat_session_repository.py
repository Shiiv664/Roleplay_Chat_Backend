"""Tests for the ChatSessionRepository class."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.chat_session_repository import ChatSessionRepository
from app.utils.exceptions import DatabaseError, ResourceNotFoundError


class TestChatSessionRepository:
    """Test chat session repository functionality."""

    @pytest.fixture
    def create_test_sessions(
        self,
        db_session,
        create_character,
        create_user_profile,
        create_ai_model,
        create_system_prompt,
        create_chat_session,
    ):
        """Create sample chat sessions for testing."""
        import time

        # Create entities with unique labels
        characters = []
        user_profiles = []
        ai_models = []
        system_prompts = []
        sessions = []
        timestamp = int(time.time())

        # Create three sessions with different timestamps
        base_time = datetime.utcnow()

        for i in range(3):
            # Create entities with unique labels
            character = create_character(label=f"test_char_{timestamp}_{i}")
            user_profile = create_user_profile(label=f"test_profile_{timestamp}_{i}")
            ai_model = create_ai_model(label=f"test_model_{timestamp}_{i}")
            system_prompt = create_system_prompt(label=f"test_prompt_{timestamp}_{i}")

            # Add them to the database
            db_session.add_all([character, user_profile, ai_model, system_prompt])
            db_session.flush()  # Get IDs

            # Create session with these entities
            session = create_chat_session(
                character=character,
                user_profile=user_profile,
                ai_model=ai_model,
                system_prompt=system_prompt,
            )

            # Adjust timestamps to ensure predictable ordering for tests
            session.updated_at = base_time - timedelta(hours=i)

            # Add to lists
            characters.append(character)
            user_profiles.append(user_profile)
            ai_models.append(ai_model)
            system_prompts.append(system_prompt)
            sessions.append(session)

        db_session.add_all(sessions)
        db_session.commit()

        return sessions

    def test_get_by_id_with_relations(self, db_session, create_test_sessions):
        """Test retrieving a chat session with related entities."""
        repo = ChatSessionRepository(db_session)
        sessions = create_test_sessions

        # Get session with relations
        session = repo.get_by_id_with_relations(sessions[0].id)

        # Verify session was retrieved
        assert session is not None
        assert session.id == sessions[0].id

        # Verify relations were loaded
        assert session.character is not None
        assert session.user_profile is not None
        assert session.ai_model is not None
        assert session.system_prompt is not None

    def test_get_by_id_with_relations_not_found(self, db_session):
        """Test retrieving a non-existent chat session with relations."""
        repo = ChatSessionRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.get_by_id_with_relations(999)  # Non-existent ID

    def test_get_sessions_by_character_id(self, db_session, create_test_sessions):
        """Test getting chat sessions for a specific character."""
        repo = ChatSessionRepository(db_session)
        sessions = create_test_sessions
        character_id = sessions[0].character_id

        # Get sessions by character ID
        character_sessions = repo.get_sessions_by_character_id(character_id)

        # There should be at least one session for this character
        assert len(character_sessions) >= 1
        # Verify all returned sessions belong to the character
        for session in character_sessions:
            assert session.character_id == character_id

    def test_get_sessions_by_user_profile_id(self, db_session, create_test_sessions):
        """Test getting chat sessions for a specific user profile."""
        repo = ChatSessionRepository(db_session)
        sessions = create_test_sessions
        profile_id = sessions[0].user_profile_id

        # Get sessions by user profile ID
        profile_sessions = repo.get_sessions_by_user_profile_id(profile_id)

        # There should be at least one session for this profile
        assert len(profile_sessions) >= 1
        # Verify all returned sessions belong to the user profile
        for session in profile_sessions:
            assert session.user_profile_id == profile_id

    def test_get_recent_sessions(self, db_session, create_test_sessions):
        """Test getting the most recently updated chat sessions."""
        repo = ChatSessionRepository(db_session)
        # Get recent sessions with default limit
        recent_sessions = repo.get_recent_sessions()

        # Verify sessions were returned in correct order (most recent first)
        assert len(recent_sessions) > 0
        if len(recent_sessions) > 1:
            for i in range(len(recent_sessions) - 1):
                assert (
                    recent_sessions[i].updated_at >= recent_sessions[i + 1].updated_at
                )

        # Test with custom limit
        limited_sessions = repo.get_recent_sessions(limit=1)
        assert len(limited_sessions) == 1
        assert limited_sessions[0].updated_at == recent_sessions[0].updated_at

    def test_update_session_timestamp(self, db_session, create_test_sessions):
        """Test updating a chat session's timestamp."""
        repo = ChatSessionRepository(db_session)
        sessions = create_test_sessions

        # Store the original timestamp
        original_timestamp = sessions[0].updated_at

        # Wait a moment to ensure the new timestamp will be different
        import time

        time.sleep(0.001)

        # Update timestamp
        repo.update_session_timestamp(sessions[0].id)
        db_session.commit()

        # Retrieve the updated session
        updated_session = repo.get_by_id(sessions[0].id)

        # Verify timestamp was updated
        assert updated_session.updated_at > original_timestamp

    def test_update_session_timestamp_not_found(self, db_session):
        """Test updating timestamp for a non-existent chat session."""
        repo = ChatSessionRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.update_session_timestamp(999)  # Non-existent ID

    def test_database_error_handling(self, db_session):
        """Test handling of database errors in chat session repository methods."""
        repo = ChatSessionRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_by_id_with_relations(1)

            with pytest.raises(DatabaseError):
                repo.get_sessions_by_character_id(1)

            with pytest.raises(DatabaseError):
                repo.get_sessions_by_user_profile_id(1)

            with pytest.raises(DatabaseError):
                repo.get_recent_sessions()
