"""Repository implementation for Message model."""

from typing import Dict, List, Optional, Tuple, Type

from sqlalchemy.exc import SQLAlchemyError

from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message entity."""

    def _get_model_class(self) -> Type[Message]:
        """Return the SQLAlchemy model class.

        Returns:
            Message: The Message model class
        """
        return Message

    def get_by_chat_session_id(
        self, session_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a chat session with pagination support.

        Args:
            session_id: The ID of the chat session
            limit: Maximum number of messages to return (optional)
            offset: Number of messages to skip (optional)

        Returns:
            List[Message]: List of messages for the chat session

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = (
                self.session.query(Message)
                .filter(Message.chat_session_id == session_id)
                .order_by(Message.timestamp)
            )

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving messages for chat session ID {session_id}"
            )

    def get_paged_messages(
        self, session_id: int, page: int = 1, page_size: int = 50
    ) -> Tuple[List[Message], Dict]:
        """Get paginated messages for a chat session with metadata.

        Args:
            session_id: The ID of the chat session
            page: Page number (1-based)
            page_size: Number of messages per page

        Returns:
            Tuple[List[Message], Dict]: List of messages and pagination metadata

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Get total count
            total_count = (
                self.session.query(Message)
                .filter(Message.chat_session_id == session_id)
                .count()
            )

            # Calculate pagination
            total_pages = (
                (total_count + page_size - 1) // page_size if total_count > 0 else 0
            )
            offset = (page - 1) * page_size

            # Get messages
            messages = (
                self.session.query(Message)
                .filter(Message.chat_session_id == session_id)
                .order_by(Message.timestamp.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            # Pagination metadata
            pagination = {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }

            return messages, pagination
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving paged messages for chat session ID {session_id}"
            )

    def create_bulk(self, messages_data: List[Dict]) -> List[Message]:
        """Create multiple messages in a single operation.

        Args:
            messages_data: List of dicts with message data

        Returns:
            List[Message]: List of created messages

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            message_objects = [Message(**data) for data in messages_data]
            self.session.add_all(message_objects)
            self.session.flush()
            return message_objects
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, "Error creating bulk messages")

    def get_latest_messages(self, session_id: int, count: int = 10) -> List[Message]:
        """Get the latest messages for a chat session.

        Args:
            session_id: The ID of the chat session
            count: Maximum number of messages to return

        Returns:
            List[Message]: List of latest messages in chronological order

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Get messages in reverse order then reverse the result
            messages = (
                self.session.query(Message)
                .filter(Message.chat_session_id == session_id)
                .order_by(Message.timestamp.desc())
                .limit(count)
                .all()
            )

            # Return in chronological order
            return list(reversed(messages))
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving latest messages for chat session ID {session_id}"
            )
