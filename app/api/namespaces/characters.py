"""Characters API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource
from werkzeug.datastructures import FileStorage

from app.api.models.character import (
    character_create_model,
    character_create_multipart_model,
    character_list_model,
    character_model,
    character_update_model,
    response_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.pagination import pagination_parser, search_parser
from app.repositories.character_repository import CharacterRepository
from app.services.character_service import CharacterService
from app.services.file_upload_service import FileUploadError, FileUploadService
from app.utils.db import get_db_session
from app.utils.exceptions import ValidationError

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("characters", description="Character operations")


def serialize_character(character):
    """Serialize a character object with avatar URL."""
    return {
        "id": character.id,
        "label": character.label,
        "name": character.name,
        "description": character.description,
        "avatar_image": character.avatar_image,
        "avatar_url": character.get_avatar_url(),
        "created_at": (
            character.created_at.isoformat() if character.created_at else None
        ),
        "updated_at": (
            character.updated_at.isoformat() if character.updated_at else None
        ),
    }


# Register models with namespace
api.models[character_model.name] = character_model
api.models[character_create_model.name] = character_create_model
api.models[character_create_multipart_model.name] = character_create_multipart_model
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
                paginated_characters = [
                    serialize_character(char) for char in characters[start_idx:end_idx]
                ]

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

    @api.doc(
        "create_character",
        responses={
            201: "Character created successfully",
            400: "Bad request - validation error or invalid file",
            500: "Internal server error",
        },
        params={
            "Content-Type": {
                "in": "header",
                "description": "Content type of the request",
                "type": "string",
                "enum": ["application/json", "multipart/form-data"],
                "default": "application/json",
            }
        },
    )
    @api.expect(character_create_model, validate=False)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new character with optional avatar image upload.

        ## Request Formats:

        ### 1. JSON (Content-Type: application/json)
        Standard character creation with avatar_image as URL string.
        Uses the CharacterCreate schema.

        ### 2. Multipart Form (Content-Type: multipart/form-data)
        Character creation with file upload support:
        - **label**: string (required) - Unique character identifier
        - **name**: string (required) - Character display name
        - **description**: string (optional) - Character description
        - **avatar_image**: file (optional) - Image file (PNG, JPG, GIF, WebP, max 5MB, max 1024x1024px)

        ## File Upload Details:
        - Supported formats: PNG, JPG, JPEG, GIF, WebP
        - Maximum file size: 5MB
        - Maximum dimensions: 1024x1024 pixels
        - Large images are automatically resized
        - Files are stored securely with UUID-generated names
        - Uploaded files are accessible via `/uploads/avatars/{filename}` URLs
        """
        try:
            avatar_image_path = None

            # Check if this is a multipart form request with file upload
            if request.content_type and "multipart/form-data" in request.content_type:
                # Extract form data
                label = request.form.get("label")
                name = request.form.get("name")
                description = request.form.get("description")
                avatar_file = request.files.get("avatar_image")

                # Validate required fields
                if not label or not name:
                    raise ValidationError("Label and name are required")

                # Handle file upload if provided
                if avatar_file and avatar_file.filename:
                    try:
                        file_upload_service = FileUploadService()
                        avatar_image_path = file_upload_service.save_avatar_image_sync(
                            avatar_file
                        )
                    except FileUploadError as e:
                        raise ValidationError(e.message)

                data = {
                    "label": label,
                    "name": name,
                    "description": description,
                    "avatar_image": avatar_image_path,
                }
            else:
                # Handle JSON request
                data = request.json
                if not data:
                    raise ValidationError("Request body is required")

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

                return create_response(data=serialize_character(character)), 201

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

                return create_response(data=serialize_character(character))

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

                return create_response(data=serialize_character(character))

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
                serialized_characters = [
                    serialize_character(char) for char in characters
                ]

                return create_response(
                    data=serialized_characters,
                    meta={"query": query, "count": len(characters)},
                )

        except Exception as e:
            logger.exception("Error searching characters")
            return handle_exception(e)
