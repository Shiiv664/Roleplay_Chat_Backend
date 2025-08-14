"""Characters API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

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
from app.repositories.ai_model_repository import AIModelRepository
from app.repositories.application_settings_repository import (
    ApplicationSettingsRepository,
)
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.character_service import CharacterService
from app.services.chat_session_service import ChatSessionService
from app.services.file_upload_service import FileUploadError, FileUploadService
from app.services.character_extract_service import CharacterExtractService
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
        "first_messages": character.first_messages or [],
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
                first_messages_str = request.form.get("first_messages")

                # Validate required fields
                if not label or not name:
                    raise ValidationError("Label and name are required")

                # Parse first_messages JSON string if provided
                first_messages = []
                if first_messages_str:
                    try:
                        import json

                        first_messages = json.loads(first_messages_str)
                        if not isinstance(first_messages, list):
                            raise ValidationError("first_messages must be a JSON array")
                    except json.JSONDecodeError:
                        raise ValidationError("Invalid JSON format for first_messages")

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
                    "first_messages": first_messages,
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
                    first_messages=data.get("first_messages"),
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
                    first_messages=data.get("first_messages"),
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
        """Delete a character and all associated chat sessions."""
        try:
            # Create services and repositories with session
            with get_db_session() as session:
                character_repository = CharacterRepository(session)
                chat_session_repository = ChatSessionRepository(session)
                ai_model_repository = AIModelRepository(session)
                system_prompt_repository = SystemPromptRepository(session)
                user_profile_repository = UserProfileRepository(session)
                application_settings_repository = ApplicationSettingsRepository(session)

                character_service = CharacterService(character_repository)
                chat_session_service = ChatSessionService(
                    chat_session_repository,
                    character_repository,
                    user_profile_repository,
                    ai_model_repository,
                    system_prompt_repository,
                    application_settings_repository,
                )

                # Delete character and its chat sessions
                character_service.delete_character(id, chat_session_service)

                # Commit the transaction
                session.commit()

                return create_response(
                    data={
                        "id": id,
                        "message": "Character and associated chat sessions deleted",
                    }
                )

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


@api.route("/extract-png")
class CharacterExtractPng(Resource):
    """Resource for extracting character data from PNG files."""

    @api.doc(
        "extract_character_from_png",
        responses={
            200: "Character data extracted successfully",
            400: "Bad request - invalid PNG file or no character data",
            413: "File too large",
            500: "Internal server error",
        },
        params={
            "Content-Type": {
                "in": "header",
                "description": "Must be multipart/form-data",
                "type": "string",
                "required": True,
                "default": "multipart/form-data",
            }
        },
    )
    @api.marshal_with(response_model)
    def post(self):
        """Extract character data from a PNG file containing Character Card v2 metadata.
        
        ## Overview
        This endpoint extracts character data from PNG files that contain embedded 
        Character Card v2 format metadata (chub.ai format) and returns both the 
        parsed character data and a clean avatar image.
        
        ## Request Format
        - **Content-Type**: multipart/form-data
        - **file**: PNG file with embedded Character Card v2 data (required)
        
        ## File Requirements
        - Format: PNG only
        - Maximum size: 10MB
        - Must contain Character Card v2 metadata in tEXt chunks
        - Valid image dimensions (32x32 to 2048x2048 pixels)
        
        ## Response Format
        Returns extracted character data ready for import:
        - **character_data**: Mapped character information (name, description, first_messages)
        - **avatar_image**: Clean PNG image without metadata (base64-encoded)
        - **extraction_info**: Metadata about the extraction process
        
        ## Character Card v2 Mapping
        - `data.name` → `name` (required)
        - `data.description` → `description` (required) 
        - `data.first_mes` → `first_messages[0]`
        - `data.alternate_greetings[]` → `first_messages[1:]`
        - PNG image → Clean avatar image (metadata stripped)
        - Auto-generated `label` from name + timestamp
        
        ## Error Codes
        - **INVALID_FILE_FORMAT** (400): Not a valid PNG file
        - **NO_CHARACTER_DATA** (400): PNG contains no Character Card v2 metadata
        - **INVALID_CHARACTER_DATA** (400): Character data is corrupted or invalid
        - **FILE_TOO_LARGE** (413): File exceeds 10MB limit
        - **PROCESSING_ERROR** (500): Internal error during extraction
        
        ## Usage Notes
        - This endpoint extracts data only - no database operations are performed
        - Frontend should use extracted data to prefill character creation form
        - Character creation happens through the normal POST /characters endpoint
        - Extracted avatar can be used directly or re-uploaded during character creation
        """
        try:
            # Validate request format
            if not request.content_type or "multipart/form-data" not in request.content_type:
                raise ValidationError("INVALID_REQUEST_FORMAT", "Content-Type must be multipart/form-data")
            
            # Get uploaded file
            uploaded_file = request.files.get("file")
            if not uploaded_file or not uploaded_file.filename:
                raise ValidationError("NO_FILE_PROVIDED", "PNG file is required")
            
            # Validate filename extension
            if not uploaded_file.filename.lower().endswith('.png'):
                raise ValidationError("INVALID_FILE_FORMAT", "File must be a PNG image")
            
            # Read file data
            file_data = uploaded_file.read()
            
            # Create extraction service
            extract_service = CharacterExtractService()
            
            # Validate extraction request
            extract_service.validate_extraction_request(file_data, uploaded_file.filename)
            
            # Extract character data
            extraction_result = extract_service.extract_character_from_png(file_data, uploaded_file.filename)
            
            return create_response(data=extraction_result)
            
        except Exception as e:
            logger.exception("Error extracting character from PNG")
            return handle_exception(e)
