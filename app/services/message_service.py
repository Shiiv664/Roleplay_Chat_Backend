"""Service for Message entity operations."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.services.application_settings_service import ApplicationSettingsService
from app.services.openrouter.client import OpenRouterClient
from app.services.claudecode.client import ClaudeCodeClient
from app.utils.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)

# Debug logging - controlled by environment variable
DEBUG_MESSAGE_SERVICE = os.getenv("DEBUG_MESSAGE_SERVICE", "false").lower() == "true"

if DEBUG_MESSAGE_SERVICE:
    # Set up debug logging for message service
    debug_logger = logging.getLogger("message_service_debug")
    debug_logger.setLevel(logging.DEBUG)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    debug_handler = logging.FileHandler(logs_dir / "message_service_debug.log")
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)
else:
    debug_logger = None


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
        settings_service: Optional[ApplicationSettingsService] = None,
        openrouter_client: Optional[OpenRouterClient] = None,
        claudecode_client: Optional[ClaudeCodeClient] = None,
    ):
        """Initialize the service with repositories.

        Args:
            message_repository: Repository for Message data access
            chat_session_repository: Repository for ChatSession data access
            settings_service: Service for application settings (optional)
            openrouter_client: Client for OpenRouter API (optional)
            claudecode_client: Client for Claude Code CLI (optional)
        """
        self.repository = message_repository
        self.chat_session_repository = chat_session_repository
        self.settings_service = settings_service
        self.openrouter_client = openrouter_client
        self.claudecode_client = claudecode_client

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

    def delete_message(self, message_id: int) -> int:
        """Delete a message and all subsequent messages in the conversation.

        This ensures conversation flow integrity by removing the target message
        and any messages that came after it in the chat session.

        Args:
            message_id: ID of the message to delete

        Returns:
            int: Number of messages deleted

        Raises:
            ResourceNotFoundError: If message doesn't exist
            DatabaseError: If a database error occurs
        """
        # Get current message to ensure it exists and to get the session ID
        message = self.repository.get_by_id(message_id)

        logger.info(
            f"Deleting message with ID {message_id} and all subsequent messages"
        )
        deleted_count = self.repository.delete_message_and_subsequent(message_id)

        logger.info(f"Deleted {deleted_count} messages starting from ID {message_id}")

        # Update the chat session timestamp
        self.chat_session_repository.update_session_timestamp(message.chat_session_id)

        return deleted_count

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

    def build_system_prompt(self, chat_session: ChatSession) -> str:
        """Constructs the complete system prompt for the AI model.

        Args:
            chat_session: The chat session containing all configuration

        Returns:
            Complete system prompt string

        Format:
            [pre_prompt if enabled]
            ---
            [system_prompt.content]
            ---
            [character.description]
            ---
            [user_profile.description]
        """
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("🔧 BUILDING SYSTEM PROMPT")
            debug_logger.info(f"Session ID: {chat_session.id}")

        prompt_parts = []

        # Add pre-prompt if enabled
        if chat_session.pre_prompt_enabled and chat_session.pre_prompt:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"➕ Adding pre-prompt: {chat_session.pre_prompt[:100]}..."
                )
            prompt_parts.append(chat_session.pre_prompt.strip())
        else:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info("❌ Pre-prompt disabled or empty")

        # Add system prompt
        if chat_session.system_prompt and chat_session.system_prompt.content:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"➕ Adding system prompt: {chat_session.system_prompt.content[:100]}..."
                )
            prompt_parts.append(chat_session.system_prompt.content.strip())
        else:
            logger.warning("No system prompt content available for chat session")
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.warning("⚠️ No system prompt content available")

        # Add character description
        if chat_session.character and chat_session.character.description:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"🎭 Adding character ({chat_session.character.name}): {chat_session.character.description[:100]}..."
                )
            prompt_parts.append(chat_session.character.description.strip())
        else:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info("👤 No character description - using default")
            prompt_parts.append("No character description provided")

        # Add user profile description
        if chat_session.user_profile and chat_session.user_profile.description:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"👤 Adding user profile ({chat_session.user_profile.name}): {chat_session.user_profile.description[:100]}..."
                )
            prompt_parts.append(chat_session.user_profile.description.strip())
        else:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info("👤 No user profile description - using default")
            prompt_parts.append("No user description provided")

        # Join with separator
        final_prompt = "\n---\n".join(prompt_parts)

        # Log the complete system prompt only in debug mode
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("✅ COMPLETE SYSTEM PROMPT BUILT:")
            debug_logger.info("=" * 60)
            debug_logger.info(final_prompt)
            debug_logger.info("=" * 60)

        return final_prompt

    def format_messages_for_openrouter(
        self, chat_session_id: int, new_user_message: str
    ) -> List[Dict[str, str]]:
        """Formats all messages for OpenRouter API including history and new message.

        Args:
            chat_session_id: ID of the chat session
            new_user_message: The new message from the user

        Returns:
            List of message dictionaries with 'role' and 'content' keys

        Message Order:
            1. System message (from build_system_prompt)
            2. All historical messages (user/assistant pairs)
            3. Post-prompt (if enabled) as system message
            4. New user message
        """
        # Essential logging (always enabled)
        logger.info(
            f"Formatting messages for OpenRouter - Chat Session: {chat_session_id}"
        )

        # Debug logging (only when DEBUG_MESSAGE_SERVICE=true)
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("📝 FORMATTING MESSAGES FOR OPENROUTER")
            debug_logger.info(f"Chat Session ID: {chat_session_id}")
            debug_logger.info(f"New User Message: {new_user_message[:200]}...")

        # Get chat session with all relationships
        chat_session = self.chat_session_repository.get_by_id_with_relations(
            chat_session_id
        )

        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info(f"📋 Loaded chat session: {chat_session.id}")
            debug_logger.info(
                f"🤖 AI Model: {chat_session.ai_model.label if chat_session.ai_model else 'None'}"
            )
            debug_logger.info(
                f"🎭 Character: {chat_session.character.name if chat_session.character else 'None'}"
            )
            debug_logger.info(
                f"👤 User Profile: {chat_session.user_profile.name if chat_session.user_profile else 'None'}"
            )

        # Build system prompt
        system_prompt = self.build_system_prompt(chat_session)

        # Start with system message
        messages = [{"role": "system", "content": system_prompt}]
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("✅ Added system message")

        # Get all historical messages
        history = self.repository.get_by_chat_session_id(chat_session_id)
        logger.info(f"Found {len(history)} historical messages")
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info(f"📚 Found {len(history)} historical messages")

        # Add historical messages
        for i, msg in enumerate(history):
            messages.append({"role": msg.role.value, "content": msg.content})
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"  📖 History {i+1}: {msg.role.value} - {msg.content[:100]}..."
                )

        # Add post-prompt if enabled
        if chat_session.post_prompt_enabled and chat_session.post_prompt:
            messages.append(
                {"role": "system", "content": chat_session.post_prompt.strip()}
            )
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"➕ Added post-prompt: {chat_session.post_prompt[:100]}..."
                )
        else:
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info("❌ Post-prompt disabled or empty")

        # Add new user message
        messages.append({"role": "user", "content": new_user_message})
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("➕ Added new user message")

        logger.info(f"Formatted {len(messages)} messages for OpenRouter")
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info(f"📊 FINAL MESSAGE COUNT: {len(messages)}")
            debug_logger.info("🔍 COMPLETE MESSAGE ARRAY:")
            for i, msg in enumerate(messages):
                debug_logger.info(f"  Message {i+1} ({msg['role']}):")
                debug_logger.info(
                    f"    {msg['content'][:300]}{'...' if len(msg['content']) > 300 else ''}"
                )

        return messages

    def generate_streaming_response(
        self, chat_session_id: int, user_message: str, user_message_id: int = None
    ) -> Iterator[Dict[str, Any]]:
        """Generates AI response using either OpenRouter or Claude Code CLI.

        Args:
            chat_session_id: ID of the chat session
            user_message: The user's message content
            user_message_id: ID of the saved user message (optional, will be created if None)

        Yields:
            Dictionary objects containing:
            - {"type": "user_message_saved", "user_message_id": int} - when user message is saved
            - {"type": "content", "data": str} - for each content chunk
            - {"type": "done", "ai_message_id": int} - when response is complete
            - {"type": "error", "error": str} - if an error occurs

        Side Effects:
            - Saves user message to database (if not already saved)
            - Saves completed AI message to database
            - Updates stream state management
        """
        # Get chat session with relationships to determine AI model
        chat_session = self.chat_session_repository.get_by_id_with_relations(
            chat_session_id
        )

        # Get model name
        if not chat_session.ai_model or not chat_session.ai_model.label:
            raise BusinessRuleError("AI model not configured for chat session")

        model_label = chat_session.ai_model.label

        # Route to appropriate implementation based on model label
        if model_label == "ClaudeCode":
            yield from self.generate_streaming_response_claude_code(
                chat_session_id, user_message, user_message_id
            )
        else:
            yield from self.generate_streaming_response_openrouter(
                chat_session_id, user_message, user_message_id
            )

    def generate_streaming_response_openrouter(
        self, chat_session_id: int, user_message: str, user_message_id: int = None
    ) -> Iterator[Dict[str, Any]]:
        """Generates AI response using OpenRouter streaming API.

        Args:
            chat_session_id: ID of the chat session
            user_message: The user's message content
            user_message_id: ID of the saved user message (optional, will be created if None)

        Yields:
            Dictionary objects containing:
            - {"type": "user_message_saved", "user_message_id": int} - when user message is saved
            - {"type": "content", "data": str} - for each content chunk
            - {"type": "done", "ai_message_id": int} - when response is complete
            - {"type": "error", "error": str} - if an error occurs

        Side Effects:
            - Saves user message to database (if not already saved)
            - Saves completed AI message to database
            - Updates stream state management

        Process:
            1. Get chat session with all relationships
            2. Save user message if not already saved
            3. Build system prompt using chat session config
            4. Format message history + new message
            5. Get model name from chat_session.ai_model.label
            6. Call OpenRouter streaming API
            7. Yield chunks as they arrive
            8. Save complete response to database
            9. Yield completion event with AI message ID
        """
        # Check dependencies
        if not self.settings_service:
            raise BusinessRuleError("Settings service not available")
        if not self.openrouter_client:
            raise BusinessRuleError("OpenRouter client not available")

        # Get OpenRouter API key
        api_key = self.settings_service.get_openrouter_api_key()
        if not api_key:
            raise BusinessRuleError("OpenRouter API key not configured")

        # Get chat session with relationships
        chat_session = self.chat_session_repository.get_by_id_with_relations(
            chat_session_id
        )

        # Get model name
        if not chat_session.ai_model or not chat_session.ai_model.label:
            raise BusinessRuleError("AI model not configured for chat session")

        model_name = chat_session.ai_model.label

        # Save the user message to database if not already saved
        if user_message_id is None:
            user_message_obj = self.create_user_message(chat_session_id, user_message)
            try:
                self.repository.session.commit()
                logger.info("Saved user message to database")
                if DEBUG_MESSAGE_SERVICE and debug_logger:
                    debug_logger.info(
                        f"✅ Saved user message to database: {user_message_obj.id}"
                    )
                # Yield the user message saved event
                yield {
                    "type": "user_message_saved",
                    "user_message_id": user_message_obj.id,
                }
            except Exception as commit_error:
                self.repository.session.rollback()
                logger.error(f"Failed to save user message: {commit_error}")
                if DEBUG_MESSAGE_SERVICE and debug_logger:
                    debug_logger.error(
                        f"❌ Failed to save user message: {commit_error}"
                    )
                yield {"type": "error", "error": "Failed to save user message"}
                return

        # Format messages for OpenRouter
        messages = self.format_messages_for_openrouter(chat_session_id, user_message)

        # Accumulate response for saving
        accumulated_response = ""
        ai_message_obj = None

        try:
            # Stream response from OpenRouter
            for chunk in self.openrouter_client.chat_completion_stream(
                model=model_name, messages=messages
            ):
                # Extract content from chunk
                if chunk.get("choices") and chunk["choices"][0].get("delta"):
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        accumulated_response += content
                        yield {"type": "content", "data": content}

            # Save complete AI response
            if accumulated_response:
                ai_message_obj = self.create_assistant_message(
                    chat_session_id, accumulated_response
                )
                # Commit the session to ensure message is saved
                try:
                    self.repository.session.commit()
                    logger.info(f"Saved AI response to database: {ai_message_obj.id}")
                    if DEBUG_MESSAGE_SERVICE and debug_logger:
                        debug_logger.info(f"✅ Saved AI response: {ai_message_obj.id}")
                except Exception as commit_error:
                    logger.error(f"Failed to commit AI message: {commit_error}")
                    self.repository.session.rollback()
                    yield {"type": "error", "error": "Failed to save AI response"}
                    return

            # Yield completion event with AI message ID
            completion_event = {"type": "done"}
            if ai_message_obj:
                completion_event["ai_message_id"] = ai_message_obj.id
            yield completion_event

        except Exception as e:
            logger.error(f"Error during streaming response: {str(e)}")
            # Save partial response if any
            if accumulated_response:
                error_message = (
                    f"{accumulated_response}\n\n[Response interrupted due to error]"
                )
                try:
                    ai_message_obj = self.create_assistant_message(
                        chat_session_id, error_message
                    )
                    self.repository.session.commit()
                    logger.info(f"Saved partial AI response: {ai_message_obj.id}")
                except Exception as commit_error:
                    logger.error(f"Failed to commit partial message: {commit_error}")
                    self.repository.session.rollback()

            # Yield error event
            yield {"type": "error", "error": str(e)}

    def generate_streaming_response_claude_code(
        self, chat_session_id: int, user_message: str, user_message_id: int = None
    ) -> Iterator[Dict[str, Any]]:
        """Generates AI response using Claude Code CLI.

        Args:
            chat_session_id: ID of the chat session
            user_message: The user's message content
            user_message_id: ID of the saved user message (optional, will be created if None)

        Yields:
            Dictionary objects containing:
            - {"type": "user_message_saved", "user_message_id": int} - when user message is saved
            - {"type": "content", "data": str} - for each content chunk
            - {"type": "done", "ai_message_id": int} - when response is complete
            - {"type": "error", "error": str} - if an error occurs

        Side Effects:
            - Saves user message to database (if not already saved)
            - Saves completed AI message to database
            - Updates stream state management

        Process:
            1. Get chat session with all relationships
            2. Save user message if not already saved
            3. Build system prompt using chat session config
            4. Format conversation history + new message as text
            5. Call Claude Code CLI with system prompt and conversation
            6. Yield chunks as they arrive
            7. Save complete response to database
            8. Yield completion event with AI message ID
        """
        # Check dependencies
        if not self.claudecode_client:
            raise BusinessRuleError("Claude Code client not available")

        # Get chat session with relationships
        chat_session = self.chat_session_repository.get_by_id_with_relations(
            chat_session_id
        )

        # Save the user message to database if not already saved
        if user_message_id is None:
            user_message_obj = self.create_user_message(chat_session_id, user_message)
            try:
                self.repository.session.commit()
                logger.info("Saved user message to database")
                if DEBUG_MESSAGE_SERVICE and debug_logger:
                    debug_logger.info(
                        f"✅ Saved user message to database: {user_message_obj.id}"
                    )
                # Yield the user message saved event
                yield {
                    "type": "user_message_saved",
                    "user_message_id": user_message_obj.id,
                }
            except Exception as commit_error:
                self.repository.session.rollback()
                logger.error(f"Failed to save user message: {commit_error}")
                if DEBUG_MESSAGE_SERVICE and debug_logger:
                    debug_logger.error(
                        f"❌ Failed to save user message: {commit_error}"
                    )
                yield {"type": "error", "error": "Failed to save user message"}
                return

        # Build system prompt using existing logic
        system_prompt = self.build_system_prompt(chat_session)

        # Format conversation for Claude Code CLI
        conversation_text = self.format_conversation_for_claude_code(chat_session_id, user_message)

        # Accumulate response for saving
        accumulated_response = ""
        ai_message_obj = None

        try:
            # Stream response from Claude Code CLI
            for chunk in self.claudecode_client.chat_completion_stream(
                system_prompt=system_prompt, conversation_text=conversation_text
            ):
                # Extract content from assistant message chunks
                if chunk.get("type") == "assistant" and chunk.get("message"):
                    content_list = chunk["message"].get("content", [])
                    if content_list and isinstance(content_list, list):
                        for content_item in content_list:
                            if isinstance(content_item, dict) and content_item.get("text"):
                                content = content_item["text"]
                                accumulated_response += content
                                yield {"type": "content", "data": content}

            # Save complete AI response
            if accumulated_response:
                ai_message_obj = self.create_assistant_message(
                    chat_session_id, accumulated_response
                )
                # Commit the session to ensure message is saved
                try:
                    self.repository.session.commit()
                    logger.info(f"Saved AI response to database: {ai_message_obj.id}")
                    if DEBUG_MESSAGE_SERVICE and debug_logger:
                        debug_logger.info(f"✅ Saved AI response: {ai_message_obj.id}")
                except Exception as commit_error:
                    logger.error(f"Failed to commit AI message: {commit_error}")
                    self.repository.session.rollback()
                    yield {"type": "error", "error": "Failed to save AI response"}
                    return

            # Yield completion event with AI message ID
            completion_event = {"type": "done"}
            if ai_message_obj:
                completion_event["ai_message_id"] = ai_message_obj.id
            yield completion_event

        except Exception as e:
            logger.error(f"Error during Claude Code streaming response: {str(e)}")
            # Save partial response if any
            if accumulated_response:
                error_message = (
                    f"{accumulated_response}\n\n[Response interrupted due to error]"
                )
                try:
                    ai_message_obj = self.create_assistant_message(
                        chat_session_id, error_message
                    )
                    self.repository.session.commit()
                    logger.info(f"Saved partial AI response: {ai_message_obj.id}")
                except Exception as commit_error:
                    logger.error(f"Failed to commit partial message: {commit_error}")
                    self.repository.session.rollback()

            # Yield error event
            yield {"type": "error", "error": str(e)}

    def format_conversation_for_claude_code(
        self, chat_session_id: int, new_user_message: str
    ) -> str:
        """Formats all messages for Claude Code CLI as plain text conversation.

        Args:
            chat_session_id: ID of the chat session
            new_user_message: The new message from the user

        Returns:
            Plain text conversation string formatted for stdin

        Format:
            User: [message 1]
            Assistant: [response 1]
            User: [message 2]
            Assistant: [response 2]
            User: [new_user_message]
        """
        logger.info(
            f"Formatting conversation for Claude Code CLI - Chat Session: {chat_session_id}"
        )

        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("📝 FORMATTING CONVERSATION FOR CLAUDE CODE CLI")
            debug_logger.info(f"Chat Session ID: {chat_session_id}")
            debug_logger.info(f"New User Message: {new_user_message[:200]}...")

        # Get all historical messages
        history = self.repository.get_by_chat_session_id(chat_session_id)
        logger.info(f"Found {len(history)} historical messages")

        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info(f"📚 Found {len(history)} historical messages")

        # Build conversation text
        conversation_lines = []
        for msg in history:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            conversation_lines.append(f"{role}: {msg.content}")
            
            if DEBUG_MESSAGE_SERVICE and debug_logger:
                debug_logger.info(
                    f"  📖 {role}: {msg.content[:100]}..."
                )

        # Add new user message
        conversation_lines.append(f"User: {new_user_message}")
        
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info("➕ Added new user message")

        conversation_text = "\n".join(conversation_lines)
        
        logger.info(f"Formatted conversation with {len(conversation_lines)} total messages")
        
        if DEBUG_MESSAGE_SERVICE and debug_logger:
            debug_logger.info(f"📊 FINAL CONVERSATION LENGTH: {len(conversation_text)} characters")
            debug_logger.info("🔍 COMPLETE CONVERSATION TEXT:")
            debug_logger.info("=" * 60)
            debug_logger.info(conversation_text)
            debug_logger.info("=" * 60)

        return conversation_text
