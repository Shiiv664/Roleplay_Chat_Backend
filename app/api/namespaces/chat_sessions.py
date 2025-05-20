"""Chat Sessions API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.chat_session import (
    chat_session_create_model,
    chat_session_list_model,
    chat_session_model,
    chat_session_update_model,
    response_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.chat_session import recent_sessions_parser
from app.api.parsers.pagination import pagination_parser
from app.repositories.ai_model_repository import AIModelRepository
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.chat_session_service import ChatSessionService
from app.utils.db import get_db_session

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("chat-sessions", description="Chat Session operations")

# Register models with namespace
api.models[chat_session_model.name] = chat_session_model
api.models[chat_session_create_model.name] = chat_session_create_model
api.models[chat_session_update_model.name] = chat_session_update_model
api.models[chat_session_list_model.name] = chat_session_list_model
api.models[response_model.name] = response_model


@api.route("/")
class ChatSessionList(Resource):
    """Resource for multiple chat sessions."""

    @api.doc("list_chat_sessions")
    @api.expect(pagination_parser)
    @api.marshal_with(response_model)
    def get(self):
        """List all chat sessions with pagination."""
        try:
            # Parse pagination arguments
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            page_size = args.get("page_size", 20)

            # Create repository with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)

                # Get all chat sessions directly from repository
                chat_sessions = chat_session_repository.get_all()

                # Apply manual pagination
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_sessions = chat_sessions[start_idx:end_idx]

                # Create pagination metadata
                total_items = len(chat_sessions)
                total_pages = (total_items + page_size - 1) // page_size
                pagination = {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                }

                return create_response(
                    data=paginated_sessions, meta={"pagination": pagination}
                )

        except Exception as e:
            logger.exception("Error listing chat sessions")
            return handle_exception(e)

    @api.doc("create_chat_session")
    @api.expect(chat_session_create_model)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new chat session."""
        try:
            # Get request data
            data = request.json

            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Create chat session
                chat_session = chat_session_service.create_session(
                    character_id=data.get("character_id"),
                    user_profile_id=data.get("user_profile_id"),
                    ai_model_id=data.get("ai_model_id"),
                    system_prompt_id=data.get("system_prompt_id"),
                    pre_prompt=data.get("pre_prompt"),
                    pre_prompt_enabled=data.get("pre_prompt_enabled", False),
                    post_prompt=data.get("post_prompt"),
                    post_prompt_enabled=data.get("post_prompt_enabled", False),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=chat_session), 201

        except Exception as e:
            logger.exception("Error creating chat session")
            return handle_exception(e)


@api.route("/<int:id>")
@api.param("id", "The chat session identifier")
@api.response(404, "Chat session not found")
class ChatSessionItem(Resource):
    """Resource for individual chat session operations."""

    @api.doc("get_chat_session")
    @api.marshal_with(response_model)
    def get(self, id):
        """Get a chat session by ID."""
        try:
            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Get chat session with relations
                chat_session = chat_session_service.get_session_with_relations(id)

                return create_response(data=chat_session)

        except Exception as e:
            logger.exception(f"Error getting chat session {id}")
            return handle_exception(e)

    @api.doc("update_chat_session")
    @api.expect(chat_session_update_model)
    @api.marshal_with(response_model)
    def put(self, id):
        """Update a chat session."""
        try:
            # Get request data
            data = request.json

            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Update chat session
                chat_session = chat_session_service.update_session(
                    session_id=id,
                    ai_model_id=data.get("ai_model_id"),
                    system_prompt_id=data.get("system_prompt_id"),
                    pre_prompt=data.get("pre_prompt"),
                    pre_prompt_enabled=data.get("pre_prompt_enabled"),
                    post_prompt=data.get("post_prompt"),
                    post_prompt_enabled=data.get("post_prompt_enabled"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=chat_session)

        except Exception as e:
            logger.exception(f"Error updating chat session {id}")
            return handle_exception(e)

    @api.doc("delete_chat_session")
    @api.marshal_with(response_model)
    def delete(self, id):
        """Delete a chat session."""
        try:
            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Delete chat session
                chat_session_service.delete_session(id)

                # Commit the transaction
                session.commit()

                return create_response(
                    data={"id": id, "message": "Chat session deleted"}
                )

        except Exception as e:
            logger.exception(f"Error deleting chat session {id}")
            return handle_exception(e)


@api.route("/recent")
class RecentChatSessions(Resource):
    """Resource for recent chat sessions."""

    @api.doc("get_recent_chat_sessions")
    @api.expect(recent_sessions_parser)
    @api.marshal_with(response_model)
    def get(self):
        """Get recent chat sessions."""
        try:
            # Parse arguments
            args = recent_sessions_parser.parse_args()
            limit = args.get("limit", 10)

            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Get recent chat sessions
                recent_sessions = chat_session_service.get_recent_sessions(limit=limit)

                return create_response(
                    data=recent_sessions,
                    meta={"limit": limit, "count": len(recent_sessions)},
                )

        except Exception as e:
            logger.exception("Error getting recent chat sessions")
            return handle_exception(e)


@api.route("/character/<int:character_id>")
@api.param("character_id", "The character identifier")
class CharacterChatSessions(Resource):
    """Resource for chat sessions by character."""

    @api.doc("get_chat_sessions_by_character")
    @api.marshal_with(response_model)
    def get(self, character_id):
        """Get chat sessions for a specific character."""
        try:
            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Get chat sessions by character
                sessions = chat_session_service.get_sessions_by_character(character_id)

                return create_response(
                    data=sessions,
                    meta={"character_id": character_id, "count": len(sessions)},
                )

        except Exception as e:
            logger.exception(
                f"Error getting chat sessions for character {character_id}"
            )
            return handle_exception(e)


@api.route("/user-profile/<int:profile_id>")
@api.param("profile_id", "The user profile identifier")
class UserProfileChatSessions(Resource):
    """Resource for chat sessions by user profile."""

    @api.doc("get_chat_sessions_by_user_profile")
    @api.marshal_with(response_model)
    def get(self, profile_id):
        """Get chat sessions for a specific user profile."""
        try:
            # Create service and repositories with session
            with get_db_session() as session:
                chat_session_repository = ChatSessionRepository(session)
                character_repository = CharacterRepository(session)
                user_profile_repository = UserProfileRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)

                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                )

                # Get chat sessions by user profile
                sessions = chat_session_service.get_sessions_by_user_profile(profile_id)

                return create_response(
                    data=sessions,
                    meta={"user_profile_id": profile_id, "count": len(sessions)},
                )

        except Exception as e:
            logger.exception(
                f"Error getting chat sessions for user profile {profile_id}"
            )
            return handle_exception(e)
