"""Messages API namespace definition."""

import logging
from typing import Any, Dict, Tuple

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.message import (
    message_create_model,
    message_list_model,
    message_model,
    message_update_model,
    message_with_response_model,
    response_model,
    user_message_create_model,
)
from app.api.parsers.pagination import pagination_parser
from app.models.message import MessageRole
from app.services.message_service import MessageService
from app.utils.exceptions import (
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Create the namespace
api = Namespace("messages", description="Message operations")

# Register models
api.models[message_model.name] = message_model
api.models[message_create_model.name] = message_create_model
api.models[message_update_model.name] = message_update_model
api.models[message_with_response_model.name] = message_with_response_model
api.models[message_list_model.name] = message_list_model
api.models[response_model.name] = response_model
api.models[user_message_create_model.name] = user_message_create_model


def get_message_service() -> MessageService:
    """Create and return a MessageService instance.

    This is a factory function that creates a new MessageService
    with its required dependencies.

    Returns:
        MessageService: An initialized message service
    """
    from app.repositories.chat_session_repository import ChatSessionRepository
    from app.repositories.message_repository import MessageRepository
    from app.utils.db import get_session

    db_session = get_session()
    message_repo = MessageRepository(db_session)
    chat_session_repo = ChatSessionRepository(db_session)
    return MessageService(message_repo, chat_session_repo)


def format_message_data(message):
    """Format a message object for API response.

    Args:
        message: The message object to format

    Returns:
        Dict: Formatted message data
    """
    return {
        "id": message.id,
        "chat_session_id": message.chat_session_id,
        "role": message.role.value,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
    }


def error_response(status_code, message, error_code=None, details=None):
    """Create a properly formatted error response with success=False.

    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Custom error code identifier (RESOURCE_NOT_FOUND, etc.)
        details: Any additional error details

    Returns:
        Tuple: Response dictionary and status code
    """
    response = {
        "success": False,
        "error": {
            "code": error_code or "UNKNOWN_ERROR",
            "message": message,
        },
    }

    if details:
        response["error"]["details"] = details

    return response, status_code


@api.route("/<int:message_id>")
@api.param("message_id", "The message identifier")
class MessageResource(Resource):
    """Resource for individual messages."""

    @api.doc("get_message")
    @api.response(200, "Success", response_model)
    @api.response(404, "Message not found")
    def get(self, message_id: int) -> Dict[str, Any]:
        """Get a message by ID.

        Args:
            message_id: The message ID

        Returns:
            The message data
        """
        try:
            message_service = get_message_service()
            message = message_service.get_message(message_id)
            return {
                "success": True,
                "data": format_message_data(message),
            }
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("update_message")
    @api.expect(message_update_model)
    @api.response(200, "Success", response_model)
    @api.response(400, "Validation error")
    @api.response(404, "Message not found")
    def put(self, message_id: int) -> Dict[str, Any]:
        """Update a message.

        Only the content can be updated, not the role or chat session.

        Args:
            message_id: The message ID

        Returns:
            The updated message data
        """
        try:
            message_service = get_message_service()
            content = request.json.get("content")
            message = message_service.update_message(message_id, content)
            return {
                "success": True,
                "data": format_message_data(message),
            }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except BusinessRuleError as e:
            return error_response(403, e.message, "BUSINESS_RULE_ERROR")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("delete_message")
    @api.response(200, "Success", response_model)
    @api.response(404, "Message not found")
    def delete(self, message_id: int) -> Dict[str, Any]:
        """Delete a message.

        Args:
            message_id: The message ID

        Returns:
            Success message
        """
        try:
            message_service = get_message_service()
            message_service.delete_message(message_id)
            return {
                "success": True,
                "data": {"message": "Message deleted successfully"},
            }
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/chat-sessions/<int:chat_session_id>")
@api.param("chat_session_id", "The chat session identifier")
class ChatSessionMessagesResource(Resource):
    """Resource for messages within a chat session."""

    @api.doc("get_messages")
    @api.expect(pagination_parser)
    @api.response(200, "Success", response_model)
    @api.response(400, "Validation error")
    @api.response(404, "Chat session not found")
    def get(self, chat_session_id: int) -> Dict[str, Any]:
        """Get messages for a chat session.

        Args:
            chat_session_id: The chat session ID

        Returns:
            List of messages with pagination
        """
        try:
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            per_page = args.get("per_page", 50)

            message_service = get_message_service()
            messages, pagination = message_service.get_paged_messages(
                chat_session_id, page, per_page
            )

            return {
                "success": True,
                "data": {
                    "items": [format_message_data(msg) for msg in messages],
                    "pagination": pagination,
                },
            }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("create_message")
    @api.expect(message_create_model)
    @api.response(201, "Message created", response_model)
    @api.response(400, "Validation error")
    @api.response(404, "Chat session not found")
    def post(self, chat_session_id: int) -> Tuple[Dict[str, Any], int]:
        """Create a new message in a chat session.

        Args:
            chat_session_id: The chat session ID

        Returns:
            The created message data
        """
        try:
            data = request.json
            role_str = data.get("role")
            content = data.get("content")

            message_service = get_message_service()
            message = message_service.create_message(chat_session_id, role_str, content)

            return {
                "success": True,
                "data": format_message_data(message),
            }, 201
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/chat-sessions/<int:chat_session_id>/user-message")
@api.param("chat_session_id", "The chat session identifier")
class UserMessageResource(Resource):
    """Resource for creating user messages with AI responses."""

    @api.doc("create_user_message")
    @api.expect(user_message_create_model)
    @api.response(201, "Message created", response_model)
    @api.response(400, "Validation error")
    @api.response(404, "Chat session not found")
    def post(self, chat_session_id: int) -> Tuple[Dict[str, Any], int]:
        """Create a user message and generate an AI response.

        Args:
            chat_session_id: The chat session ID

        Returns:
            Both user message and AI response
        """
        try:
            content = request.json.get("content")

            message_service = get_message_service()

            # Create user message
            user_message = message_service.create_user_message(chat_session_id, content)

            # In a real implementation, this would trigger AI generation
            # For now, we'll create a placeholder AI response
            ai_message = message_service.create_assistant_message(
                chat_session_id,
                "This is a placeholder AI response. In a real implementation, "
                "this would be generated by calling the AI model.",
            )

            return {
                "success": True,
                "data": {
                    "user_message": format_message_data(user_message),
                    "ai_message": format_message_data(ai_message),
                },
            }, 201
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/chat-sessions/<int:chat_session_id>/regenerate")
@api.param("chat_session_id", "The chat session identifier")
class RegenerateResponseResource(Resource):
    """Resource for regenerating AI responses."""

    @api.doc("regenerate_response")
    @api.response(200, "Success", response_model)
    @api.response(404, "Chat session not found or no messages to regenerate")
    def post(self, chat_session_id: int) -> Dict[str, Any]:
        """Regenerate the most recent AI response.

        Args:
            chat_session_id: The chat session ID

        Returns:
            The new AI response
        """
        try:
            message_service = get_message_service()

            # Get latest messages to find the last AI message
            latest_messages = message_service.get_latest_messages(chat_session_id, 10)

            # Find the most recent assistant message
            assistant_messages = [
                msg for msg in latest_messages if msg.role == MessageRole.ASSISTANT
            ]

            if not assistant_messages:
                api.abort(404, "No assistant messages found to regenerate")

            last_assistant_msg = assistant_messages[0]

            # In a real implementation, this would trigger AI regeneration
            # For now, we'll update with a placeholder
            updated_message = message_service.update_message(
                last_assistant_msg.id,
                "This is a regenerated response. In a real implementation, "
                "this would be generated by calling the AI model again.",
            )

            return {
                "success": True,
                "data": format_message_data(updated_message),
            }
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/chat-sessions/<int:chat_session_id>/latest")
@api.param("chat_session_id", "The chat session identifier")
class LatestMessagesResource(Resource):
    """Resource for retrieving the latest messages from a chat session."""

    @api.doc("get_latest_messages")
    @api.response(200, "Success", response_model)
    @api.response(404, "Chat session not found")
    def get(self, chat_session_id: int) -> Dict[str, Any]:
        """Get the latest messages from a chat session.

        Args:
            chat_session_id: The chat session ID

        Returns:
            List of latest messages
        """
        try:
            # Get count parameter, default to 10 if not provided
            count = request.args.get("count", 10, type=int)

            message_service = get_message_service()
            messages = message_service.get_latest_messages(chat_session_id, count)

            return {
                "success": True,
                "data": {
                    "items": [format_message_data(msg) for msg in messages],
                },
            }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")
