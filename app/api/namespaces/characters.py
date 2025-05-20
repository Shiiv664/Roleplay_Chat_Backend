"""Characters API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.character import (
    character_create_model,
    character_list_model,
    character_model,
    character_update_model,
    response_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.pagination import pagination_parser, search_parser
from app.repositories.character_repository import CharacterRepository
from app.services.character_service import CharacterService
from app.utils.db import get_db_session

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("characters", description="Character operations")

# Register models with namespace
api.models[character_model.name] = character_model
api.models[character_create_model.name] = character_create_model
api.models[character_update_model.name] = character_update_model
api.models[character_list_model.name] = character_list_model
api.models[response_model.name] = response_model


@api.route("/")
class CharacterList(Resource):
    """Resource for multiple characters."""

    @api.doc("list_characters")
    @api.expect(pagination_parser)
    @api.marshal_with(response_model)
    def get(self):
        """List all characters with pagination."""
        try:
            # Parse pagination arguments
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            page_size = args.get("page_size", 20)

            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Get characters with pagination
                characters = character_service.get_all_characters()

                # Apply manual pagination (in the future, implement service-level pagination)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_characters = characters[start_idx:end_idx]

                # Create pagination metadata
                total_items = len(characters)
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
                    data=paginated_characters, meta={"pagination": pagination}
                )

        except Exception as e:
            logger.exception("Error listing characters")
            return handle_exception(e)

    @api.doc("create_character")
    @api.expect(character_create_model)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new character."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Create character
                character = character_service.create_character(
                    label=data.get("label"),
                    name=data.get("name"),
                    description=data.get("description"),
                    avatar_image=data.get("avatar_image"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=character), 201

        except Exception as e:
            logger.exception("Error creating character")
            return handle_exception(e)


@api.route("/<int:id>")
@api.param("id", "The character identifier")
@api.response(404, "Character not found")
class CharacterItem(Resource):
    """Resource for individual character operations."""

    @api.doc("get_character")
    @api.marshal_with(response_model)
    def get(self, id):
        """Get a character by ID."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Get character
                character = character_service.get_character(id)

                return create_response(data=character)

        except Exception as e:
            logger.exception(f"Error getting character {id}")
            return handle_exception(e)

    @api.doc("update_character")
    @api.expect(character_update_model)
    @api.marshal_with(response_model)
    def put(self, id):
        """Update a character."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Update character
                character = character_service.update_character(
                    character_id=id,
                    label=data.get("label"),
                    name=data.get("name"),
                    description=data.get("description"),
                    avatar_image=data.get("avatar_image"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=character)

        except Exception as e:
            logger.exception(f"Error updating character {id}")
            return handle_exception(e)

    @api.doc("delete_character")
    @api.marshal_with(response_model)
    def delete(self, id):
        """Delete a character."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Delete character
                character_service.delete_character(id)

                # Commit the transaction
                session.commit()

                return create_response(data={"id": id, "message": "Character deleted"})

        except Exception as e:
            logger.exception(f"Error deleting character {id}")
            return handle_exception(e)


@api.route("/search")
class CharacterSearch(Resource):
    """Resource for searching characters."""

    @api.doc("search_characters")
    @api.expect(search_parser)
    @api.marshal_with(response_model)
    def get(self):
        """Search for characters by name or description."""
        try:
            # Parse search arguments
            args = search_parser.parse_args()
            query = args.get("query", "")

            # Create service and repository with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                character_service = CharacterService(character_repository)

                # Search characters
                characters = character_service.search_characters(query)

                return create_response(
                    data=characters, meta={"query": query, "count": len(characters)}
                )

        except Exception as e:
            logger.exception("Error searching characters")
            return handle_exception(e)
