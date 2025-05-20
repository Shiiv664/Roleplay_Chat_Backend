"""AI Models API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.ai_model import (
    ai_model_create_model,
    ai_model_list_model,
    ai_model_model,
    ai_model_update_model,
    response_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.pagination import pagination_parser, search_parser
from app.repositories.ai_model_repository import AIModelRepository
from app.services.ai_model_service import AIModelService
from app.utils.db import get_db_session

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("ai-models", description="AI Model operations")

# Register models with namespace
api.models[ai_model_model.name] = ai_model_model
api.models[ai_model_create_model.name] = ai_model_create_model
api.models[ai_model_update_model.name] = ai_model_update_model
api.models[ai_model_list_model.name] = ai_model_list_model
api.models[response_model.name] = response_model


@api.route("/")
class AIModelList(Resource):
    """Resource for multiple AI models."""

    @api.doc("list_ai_models")
    @api.expect(pagination_parser)
    @api.marshal_with(response_model)
    def get(self):
        """List all AI models with pagination."""
        try:
            # Parse pagination arguments
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            page_size = args.get("page_size", 20)

            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Get AI models with pagination
                ai_models = ai_model_service.get_all_models()

                # Apply manual pagination (in the future, implement service-level pagination)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_models = ai_models[start_idx:end_idx]

                # Create pagination metadata
                total_items = len(ai_models)
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
                    data=paginated_models, meta={"pagination": pagination}
                )

        except Exception as e:
            logger.exception("Error listing AI models")
            return handle_exception(e)

    @api.doc("create_ai_model")
    @api.expect(ai_model_create_model)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new AI model."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Create AI model
                ai_model = ai_model_service.create_model(
                    label=data.get("label"), description=data.get("description")
                )

                # Commit the transaction
                session.commit()

                return create_response(data=ai_model), 201

        except Exception as e:
            logger.exception("Error creating AI model")
            return handle_exception(e)


@api.route("/<int:id>")
@api.param("id", "The AI model identifier")
@api.response(404, "AI model not found")
class AIModelItem(Resource):
    """Resource for individual AI model operations."""

    @api.doc("get_ai_model")
    @api.marshal_with(response_model)
    def get(self, id):
        """Get an AI model by ID."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Get AI model
                ai_model = ai_model_service.get_model(id)

                return create_response(data=ai_model)

        except Exception as e:
            logger.exception(f"Error getting AI model {id}")
            return handle_exception(e)

    @api.doc("update_ai_model")
    @api.expect(ai_model_update_model)
    @api.marshal_with(response_model)
    def put(self, id):
        """Update an AI model."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Update AI model
                ai_model = ai_model_service.update_model(
                    model_id=id,
                    label=data.get("label"),
                    description=data.get("description"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=ai_model)

        except Exception as e:
            logger.exception(f"Error updating AI model {id}")
            return handle_exception(e)

    @api.doc("delete_ai_model")
    @api.marshal_with(response_model)
    def delete(self, id):
        """Delete an AI model."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Delete AI model
                ai_model_service.delete_model(id)

                # Commit the transaction
                session.commit()

                return create_response(data={"id": id, "message": "AI model deleted"})

        except Exception as e:
            logger.exception(f"Error deleting AI model {id}")
            return handle_exception(e)


@api.route("/search")
class AIModelSearch(Resource):
    """Resource for searching AI models."""

    @api.doc("search_ai_models")
    @api.expect(search_parser)
    @api.marshal_with(response_model)
    def get(self):
        """Search for AI models by label or description."""
        try:
            # Parse search arguments
            args = search_parser.parse_args()
            query = args.get("query", "")

            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Search AI models
                ai_models = ai_model_service.search_models(query)

                return create_response(
                    data=ai_models, meta={"query": query, "count": len(ai_models)}
                )

        except Exception as e:
            logger.exception("Error searching AI models")
            return handle_exception(e)


@api.route("/default")
class DefaultAIModel(Resource):
    """Resource for the default AI model."""

    @api.doc("get_default_ai_model")
    @api.marshal_with(response_model)
    def get(self):
        """Get the default AI model."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                ai_model_repository = AIModelRepository(session)
                ai_model_service = AIModelService(ai_model_repository)

                # Get default AI model
                default_model = ai_model_service.get_default_model()

                if not default_model:
                    return (
                        create_response(
                            success=False,
                            error={
                                "code": "RESOURCE_NOT_FOUND",
                                "message": "No default AI model is set",
                            },
                        ),
                        404,
                    )

                return create_response(data=default_model)

        except Exception as e:
            logger.exception("Error getting default AI model")
            return handle_exception(e)
