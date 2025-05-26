"""Repository implementation for ChatSession model."""

from datetime import datetime
from typing import List, Type

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.chat_session import ChatSession
from app.models.message import Message
from app.repositories.base_repository import BaseRepository
from app.utils.exceptions import ResourceNotFoundError


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession entity."""

    def _get_model_class(self) -> Type[ChatSession]:
        """Return the SQLAlchemy model class.

        Returns:
            ChatSession: The ChatSession model class
        """
        return ChatSession

    def get_by_id_with_relations(self, session_id: int) -> ChatSession:
        """Get chat session by ID with related entities preloaded.

        Args:
            session_id: The ID of the chat session

        Returns:
            ChatSession: The chat session with related entities loaded

        Raises:
            ResourceNotFoundError: If chat session with given ID is not found
            DatabaseError: If a database error occurs
        """
        try:
            session = (
                self.session.query(ChatSession)
                .options(
                    joinedload(ChatSession.character),
                    joinedload(ChatSession.user_profile),
                    joinedload(ChatSession.ai_model),
                    joinedload(ChatSession.system_prompt),
                )
                .filter(ChatSession.id == session_id)
                .first()
            )

            if not session:
                raise ResourceNotFoundError(
                    f"ChatSession with ID {session_id} not found"
                )

            return session
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving chat session with ID {session_id}"
            )

    def get_sessions_by_character_id(self, character_id: int) -> List[ChatSession]:
        """Get all chat sessions for a character.

        Args:
            character_id: The ID of the character

        Returns:
            List[ChatSession]: List of chat sessions for the character

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(ChatSession)
                .filter(ChatSession.character_id == character_id)
                .order_by(ChatSession.updated_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving chat sessions for character ID {character_id}"
            )

    def get_sessions_by_character_id_with_data(
        self, character_id: int
    ) -> List[ChatSession]:
        """Get all chat sessions for a character with additional data like message count.

        Args:
            character_id: The ID of the character

        Returns:
            List[ChatSession]: List of chat sessions for the character with message_count attribute

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            sessions = (
                self.session.query(
                    ChatSession, func.count(Message.id).label("message_count")
                )
                .outerjoin(Message, ChatSession.id == Message.chat_session_id)
                .filter(ChatSession.character_id == character_id)
                .group_by(ChatSession.id)
                .order_by(ChatSession.updated_at.desc())
                .all()
            )

            # Add message_count as an attribute to each session
            result_sessions = []
            for session, message_count in sessions:
                session.message_count = message_count
                result_sessions.append(session)

            return result_sessions
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e,
                f"Error retrieving chat sessions with data for character ID {character_id}",
            )

    def get_sessions_by_user_profile_id(self, profile_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user profile.

        Args:
            profile_id: The ID of the user profile

        Returns:
            List[ChatSession]: List of chat sessions for the user profile

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(ChatSession)
                .filter(ChatSession.user_profile_id == profile_id)
                .order_by(ChatSession.updated_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving chat sessions for profile ID {profile_id}"
            )

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently updated chat sessions.

        Args:
            limit: Maximum number of sessions to return (default 10)

        Returns:
            List[ChatSession]: List of most recently updated chat sessions

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(ChatSession)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving recent chat sessions")

    def get_recent_sessions_with_data(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently updated chat sessions with additional data like message count.

        Args:
            limit: Maximum number of sessions to return (default 10)

        Returns:
            List[ChatSession]: List of most recently updated chat sessions with message_count attribute

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            sessions = (
                self.session.query(
                    ChatSession, func.count(Message.id).label("message_count")
                )
                .outerjoin(Message, ChatSession.id == Message.chat_session_id)
                .group_by(ChatSession.id)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
                .all()
            )

            # Add message_count as an attribute to each session
            result_sessions = []
            for session, message_count in sessions:
                session.message_count = message_count
                result_sessions.append(session)

            return result_sessions
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, "Error retrieving recent chat sessions with data"
            )

    def update_session_timestamp(self, session_id: int) -> None:
        """Update the updated_at timestamp for a chat session.

        Args:
            session_id: The ID of the chat session

        Raises:
            ResourceNotFoundError: If chat session with given ID is not found
            DatabaseError: If a database error occurs
        """
        try:
            session = self.get_by_id(session_id)
            session.updated_at = datetime.utcnow()
            self.session.flush()
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(
                e, f"Error updating timestamp for chat session ID {session_id}"
            )
