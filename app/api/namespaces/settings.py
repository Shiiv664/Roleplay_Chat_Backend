"""Application Settings API namespace definition."""

import logging
from typing import Any, Dict

from flask import request
from flask_restx import Namespace, Resource

from app.api.models.application_settings import (
    application_settings_model,
    application_settings_reset_response_model,
    application_settings_update_model,
    application_settings_with_relations_model,
    openrouter_api_key_request_model,
    openrouter_api_key_status_model,
    openrouter_api_key_status_response_model,
    openrouter_api_key_success_model,
    openrouter_api_key_success_response_model,
    response_model,
)
from app.services.application_settings_service import ApplicationSettingsService
from app.utils.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Create the namespace
api = Namespace("settings", description="Application settings operations")

# Register models
api.models[application_settings_model.name] = application_settings_model
api.models[application_settings_with_relations_model.name] = (
    application_settings_with_relations_model
)
api.models[application_settings_update_model.name] = application_settings_update_model
api.models[application_settings_reset_response_model.name] = (
    application_settings_reset_response_model
)
api.models[response_model.name] = response_model
api.models[openrouter_api_key_request_model.name] = openrouter_api_key_request_model
api.models[openrouter_api_key_status_model.name] = openrouter_api_key_status_model
api.models[openrouter_api_key_status_response_model.name] = (
    openrouter_api_key_status_response_model
)
api.models[openrouter_api_key_success_model.name] = openrouter_api_key_success_model
api.models[openrouter_api_key_success_response_model.name] = (
    openrouter_api_key_success_response_model
)


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


def get_settings_service(session) -> ApplicationSettingsService:
    """Create and return an ApplicationSettingsService instance.

    This is a factory function that creates a new ApplicationSettingsService
    with its required dependencies.

    Args:
        session: SQLAlchemy session to use for database operations

    Returns:
        ApplicationSettingsService: An initialized settings service
    """
    from app.repositories.ai_model_repository import AIModelRepository
    from app.repositories.application_settings_repository import (
        ApplicationSettingsRepository,
    )
    from app.repositories.system_prompt_repository import SystemPromptRepository
    from app.repositories.user_profile_repository import UserProfileRepository

    settings_repo = ApplicationSettingsRepository(session)
    ai_model_repo = AIModelRepository(session)
    system_prompt_repo = SystemPromptRepository(session)
    user_profile_repo = UserProfileRepository(session)

    return ApplicationSettingsService(
        settings_repo, ai_model_repo, system_prompt_repo, user_profile_repo
    )


def format_settings_response(settings):
    """Format application settings for response.

    Args:
        settings: ApplicationSettings instance

    Returns:
        Dict: Formatted settings data
    """
    data = {
        "id": settings.id,
        "default_ai_model_id": settings.default_ai_model_id,
        "default_system_prompt_id": settings.default_system_prompt_id,
        "default_user_profile_id": settings.default_user_profile_id,
        "default_avatar_image": settings.default_avatar_image,
        "has_openrouter_api_key": bool(settings.openrouter_api_key_encrypted),
    }

    # Add related entities if they exist
    if settings.default_ai_model:
        data["default_ai_model"] = {
            "id": settings.default_ai_model.id,
            "label": settings.default_ai_model.label,
            "description": settings.default_ai_model.description,
        }

    if settings.default_system_prompt:
        data["default_system_prompt"] = {
            "id": settings.default_system_prompt.id,
            "label": settings.default_system_prompt.label,
            "content": settings.default_system_prompt.content,
        }

    if settings.default_user_profile:
        data["default_user_profile"] = {
            "id": settings.default_user_profile.id,
            "label": settings.default_user_profile.label,
            "name": settings.default_user_profile.name,
            "avatar_image": settings.default_user_profile.avatar_image,
        }

    return data


@api.route("/")
class ApplicationSettingsResource(Resource):
    """Resource for application settings."""

    @api.doc("get_settings")
    @api.response(200, "Success", response_model)
    def get(self) -> Dict[str, Any]:
        """Get the application settings.

        Returns:
            The application settings data
        """
        from app.utils.db import session_scope

        try:
            with session_scope() as session:
                settings_service = get_settings_service(session)
                settings = settings_service.get_settings()

                return {
                    "success": True,
                    "data": format_settings_response(settings),
                }
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("update_settings")
    @api.expect(application_settings_update_model)
    @api.response(200, "Success", response_model)
    @api.response(400, "Validation error")
    @api.response(404, "Referenced entity not found")
    def put(self) -> Dict[str, Any]:
        """Update the application settings.

        Returns:
            The updated application settings data
        """
        from app.utils.db import session_scope

        try:
            data = request.json or {}

            with session_scope() as session:
                settings_service = get_settings_service(session)

                # Extract the fields to update
                default_ai_model_id = data.get("default_ai_model_id")
                default_system_prompt_id = data.get("default_system_prompt_id")
                default_user_profile_id = data.get("default_user_profile_id")
                default_avatar_image = data.get("default_avatar_image")

                # Only include fields that were actually provided in the request
                update_kwargs = {}
                if "default_ai_model_id" in data:
                    update_kwargs["default_ai_model_id"] = default_ai_model_id
                if "default_system_prompt_id" in data:
                    update_kwargs["default_system_prompt_id"] = default_system_prompt_id
                if "default_user_profile_id" in data:
                    update_kwargs["default_user_profile_id"] = default_user_profile_id
                if "default_avatar_image" in data:
                    update_kwargs["default_avatar_image"] = default_avatar_image

                # Update the settings with provided values
                updated_settings = settings_service.update_settings(**update_kwargs)

                return {
                    "success": True,
                    "data": format_settings_response(updated_settings),
                }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except ResourceNotFoundError as e:
            return error_response(404, e.message, "RESOURCE_NOT_FOUND")
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/reset")
class ResetSettingsResource(Resource):
    """Resource for resetting application settings."""

    @api.doc("reset_settings")
    @api.response(200, "Success", response_model)
    def post(self) -> Dict[str, Any]:
        """Reset the application settings to defaults.

        Returns:
            Success message and reset settings
        """
        from app.utils.db import session_scope

        try:
            with session_scope() as session:
                settings_service = get_settings_service(session)
                reset_settings = settings_service.reset_settings()

                return {
                    "success": True,
                    "data": {
                        "message": "Application settings reset to defaults",
                        "settings": {
                            "id": reset_settings.id,
                            "default_ai_model_id": reset_settings.default_ai_model_id,
                            "default_system_prompt_id": reset_settings.default_system_prompt_id,
                            "default_user_profile_id": reset_settings.default_user_profile_id,
                            "default_avatar_image": reset_settings.default_avatar_image,
                        },
                    },
                }
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")


@api.route("/openrouter-api-key")
class OpenRouterAPIKeyResource(Resource):
    """Resource for managing OpenRouter API key."""

    @api.doc("get_openrouter_api_key_status")
    @api.marshal_with(response_model)
    def get(self) -> Dict[str, Any]:
        """Get OpenRouter API key status.

        Returns:
            Status indicating whether an API key is configured
        """
        from app.utils.db import session_scope

        try:
            with session_scope() as session:
                settings_service = get_settings_service(session)
                api_key = settings_service.get_openrouter_api_key()

                return {
                    "success": True,
                    "data": {
                        "has_api_key": api_key is not None,
                        "key_length": len(api_key) if api_key else 0,
                    },
                }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("set_openrouter_api_key")
    @api.expect(openrouter_api_key_request_model)
    @api.marshal_with(response_model)
    @api.response(400, "Validation error")
    def put(self) -> Dict[str, Any]:
        """Set OpenRouter API key.

        Returns:
            Success confirmation
        """
        from app.utils.db import session_scope

        try:
            data = request.json or {}
            api_key = data.get("api_key")

            if not api_key:
                return error_response(
                    400,
                    "API key is required",
                    "VALIDATION_ERROR",
                    {"api_key": "This field is required"},
                )

            with session_scope() as session:
                settings_service = get_settings_service(session)
                settings_service.set_openrouter_api_key(api_key)

                return {
                    "success": True,
                    "data": {"message": "OpenRouter API key set successfully"},
                }
        except ValidationError as e:
            return error_response(400, e.message, "VALIDATION_ERROR", e.details)
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")

    @api.doc("clear_openrouter_api_key")
    @api.marshal_with(response_model)
    def delete(self) -> Dict[str, Any]:
        """Clear OpenRouter API key.

        Returns:
            Success confirmation
        """
        from app.utils.db import session_scope

        try:
            with session_scope() as session:
                settings_service = get_settings_service(session)
                settings_service.clear_openrouter_api_key()

                return {
                    "success": True,
                    "data": {"message": "OpenRouter API key cleared successfully"},
                }
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return error_response(500, "Database error occurred", "DATABASE_ERROR")
