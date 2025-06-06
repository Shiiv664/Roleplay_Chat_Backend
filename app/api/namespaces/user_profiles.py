"""User Profiles API namespace and endpoints."""

import logging

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.user_profile import (
    response_model,
    user_profile_create_model,
    user_profile_create_multipart_model,
    user_profile_list_model,
    user_profile_model,
    user_profile_update_model,
)
from app.api.namespaces import create_response, handle_exception
from app.api.parsers.pagination import pagination_parser, search_parser
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.file_upload_service import FileUploadError, FileUploadService
from app.services.user_profile_service import UserProfileService
from app.utils.db import get_db_session
from app.utils.exceptions import ValidationError

# Initialize logger
logger = logging.getLogger(__name__)

# Create namespace
api = Namespace("user-profiles", description="User Profile operations")


def serialize_user_profile(user_profile):
    """Serialize a user profile object with avatar URL."""
    return {
        "id": user_profile.id,
        "label": user_profile.label,
        "name": user_profile.name,
        "description": user_profile.description,
        "avatar_image": user_profile.avatar_image,
        "avatar_url": user_profile.get_avatar_url(),
        "created_at": (
            user_profile.created_at.isoformat() if user_profile.created_at else None
        ),
        "updated_at": (
            user_profile.updated_at.isoformat() if user_profile.updated_at else None
        ),
    }


# Register models with namespace
api.models[user_profile_model.name] = user_profile_model
api.models[user_profile_create_model.name] = user_profile_create_model
api.models[user_profile_create_multipart_model.name] = (
    user_profile_create_multipart_model
)
api.models[user_profile_update_model.name] = user_profile_update_model
api.models[user_profile_list_model.name] = user_profile_list_model
api.models[response_model.name] = response_model


@api.route("/")
class UserProfileList(Resource):
    """Resource for multiple user profiles."""

    @api.doc("list_user_profiles")
    @api.expect(pagination_parser)
    @api.marshal_with(response_model)
    def get(self):
        """List all user profiles with pagination."""
        try:
            # Parse pagination arguments
            args = pagination_parser.parse_args()
            page = args.get("page", 1)
            page_size = args.get("page_size", 20)

            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Get user profiles with pagination
                user_profiles = user_profile_service.get_all_profiles()

                # Apply manual pagination (in the future, implement service-level pagination)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_profiles = [
                    serialize_user_profile(profile)
                    for profile in user_profiles[start_idx:end_idx]
                ]

                # Create pagination metadata
                total_items = len(user_profiles)
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
                    data=paginated_profiles, meta={"pagination": pagination}
                )

        except Exception as e:
            logger.exception("Error listing user profiles")
            return handle_exception(e)

    @api.doc(
        "create_user_profile",
        responses={
            201: "User profile created successfully",
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
    @api.expect(user_profile_create_model, validate=False)
    @api.marshal_with(response_model)
    def post(self):
        """Create a new user profile with optional avatar image upload.

        ## Request Formats:

        ### 1. JSON (Content-Type: application/json)
        Standard user profile creation with avatar_image as URL string.
        Uses the UserProfileCreate schema.

        ### 2. Multipart Form (Content-Type: multipart/form-data)
        User profile creation with file upload support:
        - **label**: string (required) - Unique user profile identifier
        - **name**: string (required) - User profile display name
        - **description**: string (optional) - User profile description
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
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Create user profile
                user_profile = user_profile_service.create_profile(
                    label=data.get("label"),
                    name=data.get("name"),
                    description=data.get("description"),
                    avatar_image=data.get("avatar_image"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=serialize_user_profile(user_profile)), 201

        except Exception as e:
            logger.exception("Error creating user profile")
            return handle_exception(e)


@api.route("/<int:id>")
@api.param("id", "The user profile identifier")
@api.response(404, "User profile not found")
class UserProfileItem(Resource):
    """Resource for individual user profile operations."""

    @api.doc("get_user_profile")
    @api.marshal_with(response_model)
    def get(self, id):
        """Get a user profile by ID."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Get user profile
                user_profile = user_profile_service.get_profile(id)

                return create_response(data=serialize_user_profile(user_profile))

        except Exception as e:
            logger.exception(f"Error getting user profile {id}")
            return handle_exception(e)

    @api.doc("update_user_profile")
    @api.expect(user_profile_update_model)
    @api.marshal_with(response_model)
    def put(self, id):
        """Update a user profile."""
        try:
            # Get request data
            data = request.json

            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Update user profile
                user_profile = user_profile_service.update_profile(
                    profile_id=id,
                    label=data.get("label"),
                    name=data.get("name"),
                    description=data.get("description"),
                    avatar_image=data.get("avatar_image"),
                )

                # Commit the transaction
                session.commit()

                return create_response(data=serialize_user_profile(user_profile))

        except Exception as e:
            logger.exception(f"Error updating user profile {id}")
            return handle_exception(e)

    @api.doc("delete_user_profile")
    @api.marshal_with(response_model)
    def delete(self, id):
        """Delete a user profile."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Delete user profile
                user_profile_service.delete_profile(id)

                # Commit the transaction
                session.commit()

                return create_response(
                    data={"id": id, "message": "User profile deleted"}
                )

        except Exception as e:
            logger.exception(f"Error deleting user profile {id}")
            return handle_exception(e)


@api.route("/search")
class UserProfileSearch(Resource):
    """Resource for searching user profiles."""

    @api.doc("search_user_profiles")
    @api.expect(search_parser)
    @api.marshal_with(response_model)
    def get(self):
        """Search for user profiles by name or description."""
        try:
            # Parse search arguments
            args = search_parser.parse_args()
            query = args.get("query", "")

            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Search user profiles
                user_profiles = user_profile_service.search_profiles(query)
                serialized_profiles = [
                    serialize_user_profile(profile) for profile in user_profiles
                ]

                return create_response(
                    data=serialized_profiles,
                    meta={"query": query, "count": len(user_profiles)},
                )

        except Exception as e:
            logger.exception("Error searching user profiles")
            return handle_exception(e)


@api.route("/default")
class DefaultUserProfile(Resource):
    """Resource for the default user profile."""

    @api.doc("get_default_user_profile")
    @api.marshal_with(response_model)
    def get(self):
        """Get the default user profile."""
        try:
            # Create service and repository with session
            with get_db_session() as session:
                user_profile_repository = UserProfileRepository(session)
                user_profile_service = UserProfileService(user_profile_repository)

                # Get default user profile
                default_profile = user_profile_service.get_default_profile()

                if not default_profile:
                    return (
                        create_response(
                            success=False,
                            error={
                                "code": "RESOURCE_NOT_FOUND",
                                "message": "No default user profile is set",
                            },
                        ),
                        404,
                    )

                return create_response(data=serialize_user_profile(default_profile))

        except Exception as e:
            logger.exception("Error getting default user profile")
            return handle_exception(e)
