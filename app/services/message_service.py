"""Service for Message entity operations."""

import logging
from typing import Dict, List, Optional, Tuple

from app.models.message import Message, MessageRole
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class MessageService:
    """Service for managing Message entities.

    This service implements business logic and validation for Message entities,
    using the MessageRepository for data access along with the ChatSessionRepository
    to validate and update chat sessions.
    """

    def __init__(
        self,
        message_repository: MessageRepository,
        chat_session_repository: ChatSessionRepository,
    ):
        """Initialize the service with repositories.

        Args:
            message_repository: Repository for Message data access
            chat_session_repository: Repository for ChatSession data access
        """
        self.repository = message_repository
        self.chat_session_repository = chat_session_repository

    def get_message(self, message_id: int) -> Message:
        """Get a message by ID.

        Args:
            message_id: ID of the message to retrieve

        Returns:
            Message: The requested message

        Raises:
            ResourceNotFoundError: If message with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting message with ID {message_id}")
        return self.repository.get_by_id(message_id)

    def get_messages_by_chat_session(
        self, session_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a chat session with optional pagination.

        Args:
            session_id: ID of the chat session
            limit: Maximum number of messages to return (optional)
            offset: Number of messages to skip (optional)

        Returns:
            List[Message]: List of messages for the chat session

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If pagination parameters are invalid
            DatabaseError: If a database error occurs
        """
        # Verify chat session exists
        self._verify_chat_session_exists(session_id)

        # Validate pagination parameters if provided
        if limit is not None and limit <= 0:
            raise ValidationError("Limit must be a positive integer")
        if offset is not None and offset < 0:
            raise ValidationError("Offset must be a non-negative integer")

        logger.info(f"Getting messages for chat session ID {session_id}")
        return self.repository.get_by_chat_session_id(session_id, limit, offset)

    def get_paged_messages(
        self, session_id: int, page: int = 1, page_size: int = 50
    ) -> Tuple[List[Message], Dict]:
        """Get paginated messages for a chat session with metadata.

        Args:
            session_id: ID of the chat session
            page: Page number (1-based)
            page_size: Number of messages per page

        Returns:
            Tuple[List[Message], Dict]: List of messages and pagination metadata

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If pagination parameters are invalid
            DatabaseError: If a database error occurs
        """
        # Verify chat session exists
        self._verify_chat_session_exists(session_id)

        # Validate pagination parameters
        if page <= 0:
            raise ValidationError("Page number must be a positive integer")
        if page_size <= 0:
            raise ValidationError("Page size must be a positive integer")

        logger.info(f"Getting paged messages for chat session ID {session_id}")
        return self.repository.get_paged_messages(session_id, page, page_size)

    def get_latest_messages(self, session_id: int, count: int = 10) -> List[Message]:
        """Get the latest messages for a chat session.

        Args:
            session_id: ID of the chat session
            count: Maximum number of messages to return

        Returns:
            List[Message]: List of latest messages in chronological order

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If count is invalid
            DatabaseError: If a database error occurs
        """
        # Verify chat session exists
        self._verify_chat_session_exists(session_id)

        # Validate count
        if count <= 0:
            raise ValidationError("Count must be a positive integer")

        logger.info(f"Getting latest {count} messages for chat session ID {session_id}")
        return self.repository.get_latest_messages(session_id, count)

    def create_message(
        self, session_id: int, role: MessageRole, content: str
    ) -> Message:
        """Create a new message in a chat session.

        Args:
            session_id: ID of the chat session to add the message to
            role: Role of the message sender (user or assistant)
            content: Text content of the message

        Returns:
            Message: The created message

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Verify chat session exists
        self._verify_chat_session_exists(session_id)

        # Validate content
        self._validate_message_content(content)

        # Validate role
        if not isinstance(role, MessageRole):
            try:
                role = MessageRole(role)
            except ValueError:
                raise ValidationError(
                    "Invalid message role",
                    details={
                        "role": f"Must be one of {[r.value for r in MessageRole]}"
                    },
                )

        # Create message
        message_data = {
            "chat_session_id": session_id,
            "role": role,
            "content": content,
        }

        logger.info(f"Creating {role.value} message in chat session ID {session_id}")
        message = self.repository.create(**message_data)

        # Update the chat session timestamp
        self.chat_session_repository.update_session_timestamp(session_id)

        return message

    def create_user_message(self, session_id: int, content: str) -> Message:
        """Create a new user message in a chat session.

        Args:
            session_id: ID of the chat session to add the message to
            content: Text content of the message

        Returns:
            Message: The created message

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        return self.create_message(session_id, MessageRole.USER, content)

    def create_assistant_message(self, session_id: int, content: str) -> Message:
        """Create a new assistant message in a chat session.

        Args:
            session_id: ID of the chat session to add the message to
            content: Text content of the message

        Returns:
            Message: The created message

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        return self.create_message(session_id, MessageRole.ASSISTANT, content)

    def create_bulk_messages(self, messages_data: List[Dict]) -> List[Message]:
        """Create multiple messages in a single operation.

        Args:
            messages_data: List of dictionaries with message data. Each dictionary
                must include 'chat_session_id', 'role', and 'content' keys.

        Returns:
            List[Message]: List of created messages

        Raises:
            ResourceNotFoundError: If any chat session doesn't exist
            ValidationError: If validation fails for any message
            DatabaseError: If a database error occurs
        """
        if not messages_data:
            raise ValidationError("No messages provided")

        # Track sessions to update later
        session_ids = set()
        verified_session_ids = set()

        # Validate all messages before creating any
        for i, message_data in enumerate(messages_data):
            # Check required fields
            for field in ["chat_session_id", "role", "content"]:
                if field not in message_data:
                    raise ValidationError(
                        f"Missing required field: {field}",
                        details={"index": i, "field": field},
                    )

            # Verify chat session exists (only once per unique session ID)
            session_id = message_data["chat_session_id"]
            if session_id not in verified_session_ids:
                self._verify_chat_session_exists(session_id)
                verified_session_ids.add(session_id)

            session_ids.add(session_id)

            # Validate content
            self._validate_message_content(message_data["content"])

            # Validate role
            role = message_data["role"]
            if not isinstance(role, MessageRole):
                try:
                    # If it's a string, try to convert it to enum
                    if isinstance(role, str):
                        message_data["role"] = MessageRole(role)
                    else:
                        raise ValueError("Role must be a string or MessageRole enum")
                except ValueError:
                    raise ValidationError(
                        "Invalid message role",
                        details={
                            "index": i,
                            "role": f"Must be one of {[r.value for r in MessageRole]}",
                        },
                    )

        # Create all messages
        logger.info(f"Creating {len(messages_data)} messages in bulk")
        messages = self.repository.create_bulk(messages_data)

        # Update timestamp for all affected chat sessions
        for session_id in session_ids:
            self.chat_session_repository.update_session_timestamp(session_id)

        return messages

    def update_message(self, message_id: int, content: str) -> Message:
        """Update an existing message.

        Only the content can be updated, not the role or chat session.

        Args:
            message_id: ID of the message to update
            content: New text content for the message

        Returns:
            Message: The updated message

        Raises:
            ResourceNotFoundError: If message doesn't exist
            ValidationError: If validation fails
            BusinessRuleError: If attempting to update a system-critical message
            DatabaseError: If a database error occurs
        """
        # Get current message
        message = self.repository.get_by_id(message_id)

        # Validate content
        self._validate_message_content(content)

        # Update the message
        logger.info(f"Updating message with ID {message_id}")
        updated_message = self.repository.update(message_id, content=content)

        # Update the chat session timestamp
        self.chat_session_repository.update_session_timestamp(message.chat_session_id)

        return updated_message

    def delete_message(self, message_id: int) -> None:
        """Delete a message.

        Args:
            message_id: ID of the message to delete

        Raises:
            ResourceNotFoundError: If message doesn't exist
            DatabaseError: If a database error occurs
        """
        # Get current message to ensure it exists and to get the session ID
        message = self.repository.get_by_id(message_id)

        logger.info(f"Deleting message with ID {message_id}")
        self.repository.delete(message_id)

        # Update the chat session timestamp
        self.chat_session_repository.update_session_timestamp(message.chat_session_id)

    def _verify_chat_session_exists(self, session_id: int) -> None:
        """Verify that a chat session exists.

        Args:
            session_id: ID of the chat session to verify

        Raises:
            ResourceNotFoundError: If chat session doesn't exist
            DatabaseError: If a database error occurs
        """
        self.chat_session_repository.get_by_id(session_id)

    def _validate_message_content(self, content: str) -> None:
        """Validate message content.

        Args:
            content: Message content to validate

        Raises:
            ValidationError: If validation fails
        """
        if not content:
            raise ValidationError(
                "Message content cannot be empty",
                details={"content": "Content must not be empty"},
            )

        if len(content) > 65535:  # Common text field size limit
            raise ValidationError(
                "Message content is too long",
                details={"content": "Content must be less than 65535 characters"},
            )
