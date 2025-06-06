"""System Prompts API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.system_prompt import (
    response_model,
    system_prompt_create_model,
    system_prompt_list_model,
    system_prompt_model,
    system_prompt_update_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.pagination import pagination_parser, search_parser
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.services.system_prompt_service import SystemPromptService
from app.utils.db import get_db_session

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("system-prompts", description="System Prompt operations")

# Register models with namespace
api.models[system_prompt_model.name] = system_prompt_model
api.models[system_prompt_create_model.name] = system_prompt_create_model
api.models[system_prompt_update_model.name] = system_prompt_update_model
api.models[system_prompt_list_model.name] = system_prompt_list_model
api.models[response_model.name] = response_model


@api.route("/")
class SystemPromptList(Resource):
    """Resource for multiple system prompts."""

    @api.doc("list_system_prompts")
    @api.expect(pagination_parser)
    @api.marshal_with(response_model)
    def get(self):
        """List all system prompts with pagination."""
        try:
            # Parse pagination arguments
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            page_size = args.get("page_size", 20)

            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Get system prompts with pagination
                system_prompts = system_prompt_service.get_all_prompts()

                # Apply manual pagination (in the future, implement service-level pagination)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_prompts = system_prompts[start_idx:end_idx]

                # Create pagination metadata
                total_items = len(system_prompts)
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
                    data=paginated_prompts, meta={"pagination": pagination}
                )

        except Exception as e:
            logger.exception("Error listing system prompts")
            return handle_exception(e)

    @api.doc("create_system_prompt")
    @api.expect(system_prompt_create_model)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new system prompt."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Create system prompt
                system_prompt = system_prompt_service.create_prompt(
                    label=data.get("label"), content=data.get("content")
                )

                # Commit the transaction
                session.commit()

                return create_response(data=system_prompt), 201

        except Exception as e:
            logger.exception("Error creating system prompt")
            return handle_exception(e)


@api.route("/<int:id>")
@api.param("id", "The system prompt identifier")
@api.response(404, "System prompt not found")
class SystemPromptItem(Resource):
    """Resource for individual system prompt operations."""

    @api.doc("get_system_prompt")
    @api.marshal_with(response_model)
    def get(self, id):
        """Get a system prompt by ID."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Get system prompt
                system_prompt = system_prompt_service.get_prompt(id)

                return create_response(data=system_prompt)

        except Exception as e:
            logger.exception(f"Error getting system prompt {id}")
            return handle_exception(e)

    @api.doc("update_system_prompt")
    @api.expect(system_prompt_update_model)
    @api.marshal_with(response_model)
    def put(self, id):
        """Update a system prompt."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Update system prompt
                system_prompt = system_prompt_service.update_prompt(
                    prompt_id=id, label=data.get("label"), content=data.get("content")
                )

                # Commit the transaction
                session.commit()

                return create_response(data=system_prompt)

        except Exception as e:
            logger.exception(f"Error updating system prompt {id}")
            return handle_exception(e)

    @api.doc("delete_system_prompt")
    @api.marshal_with(response_model)
    def delete(self, id):
        """Delete a system prompt."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Delete system prompt
                system_prompt_service.delete_prompt(id)

                # Commit the transaction
                session.commit()

                return create_response(
                    data={"id": id, "message": "System prompt deleted"}
                )

        except Exception as e:
            logger.exception(f"Error deleting system prompt {id}")
            return handle_exception(e)


@api.route("/search")
class SystemPromptSearch(Resource):
    """Resource for searching system prompts."""

    @api.doc("search_system_prompts")
    @api.expect(search_parser)
    @api.marshal_with(response_model)
    def get(self):
        """Search for system prompts by label or content."""
        try:
            # Parse search arguments
            args = search_parser.parse_args()
            query = args.get("query", "")

            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Search system prompts
                system_prompts = system_prompt_service.search_prompts(query)

                return create_response(
                    data=system_prompts,
                    meta={"query": query, "count": len(system_prompts)},
                )

        except Exception as e:
            logger.exception("Error searching system prompts")
            return handle_exception(e)


@api.route("/default")
class DefaultSystemPrompt(Resource):
    """Resource for the default system prompt."""

    @api.doc("get_default_system_prompt")
    @api.marshal_with(response_model)
    def get(self):
        """Get the default system prompt."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                system_prompt_repository = SystemPromptRepository(session)
                system_prompt_service = SystemPromptService(system_prompt_repository)

                # Get default system prompt
                default_prompt = system_prompt_service.get_default_prompt()

                if not default_prompt:
                    return (
                        create_response(
                            success=False,
                            error={
                                "code": "RESOURCE_NOT_FOUND",
                                "message": "No default system prompt is set",
                            },
                        ),
                        404,
                    )

                return create_response(data=default_prompt)

        except Exception as e:
            logger.exception("Error getting default system prompt")
            return handle_exception(e)
