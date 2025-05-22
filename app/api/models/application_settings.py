"""API models for ApplicationSettings resources."""

from flask_restx import Model, fields

from app.api.models.ai_model import ai_model_short_model
from app.api.models.system_prompt import system_prompt_short_model
from app.api.models.user_profile import user_profile_short_model

# Basic application settings model
application_settings_model = Model(
    "ApplicationSettings",
    {
        "id": fields.Integer(
            readOnly=True, description="Application Settings ID (always 1)"
        ),
        "default_ai_model_id": fields.Integer(
            required=False, description="Default AI Model ID"
        ),
        "default_system_prompt_id": fields.Integer(
            required=False, description="Default System Prompt ID"
        ),
        "default_user_profile_id": fields.Integer(
            required=False, description="Default User Profile ID"
        ),
        "default_avatar_image": fields.String(
            required=False, description="Default avatar image path or URL"
        ),
    },
)

# Application settings model with related entities
application_settings_with_relations_model = Model(
    "ApplicationSettingsWithRelations",
    {
        "id": fields.Integer(
            readOnly=True, description="Application Settings ID (always 1)"
        ),
        "default_ai_model_id": fields.Integer(
            required=False, description="Default AI Model ID"
        ),
        "default_system_prompt_id": fields.Integer(
            required=False, description="Default System Prompt ID"
        ),
        "default_user_profile_id": fields.Integer(
            required=False, description="Default User Profile ID"
        ),
        "default_avatar_image": fields.String(
            required=False, description="Default avatar image path or URL"
        ),
        "has_openrouter_api_key": fields.Boolean(
            readOnly=True, description="Whether OpenRouter API key is configured"
        ),
        "default_ai_model": fields.Nested(
            ai_model_short_model, description="Default AI Model details", skip_none=True
        ),
        "default_system_prompt": fields.Nested(
            system_prompt_short_model,
            description="Default System Prompt details",
            skip_none=True,
        ),
        "default_user_profile": fields.Nested(
            user_profile_short_model,
            description="Default User Profile details",
            skip_none=True,
        ),
    },
)

# Model for updating application settings
application_settings_update_model = Model(
    "ApplicationSettingsUpdate",
    {
        "default_ai_model_id": fields.Integer(
            required=False, description="Default AI Model ID"
        ),
        "default_system_prompt_id": fields.Integer(
            required=False, description="Default System Prompt ID"
        ),
        "default_user_profile_id": fields.Integer(
            required=False, description="Default User Profile ID"
        ),
        "default_avatar_image": fields.String(
            required=False, description="Default avatar image path or URL"
        ),
    },
)

# Response for reset operation
application_settings_reset_response_model = Model(
    "ApplicationSettingsResetResponse",
    {
        "message": fields.String(description="Success message"),
        "settings": fields.Nested(
            application_settings_model, description="Reset settings"
        ),
    },
)

# OpenRouter API key models
openrouter_api_key_request_model = Model(
    "OpenRouterAPIKeyRequest",
    {
        "api_key": fields.String(required=True, description="OpenRouter API key"),
    },
)

openrouter_api_key_status_model = Model(
    "OpenRouterAPIKeyStatus",
    {
        "has_api_key": fields.Boolean(description="Whether an API key is configured"),
        "key_length": fields.Integer(
            description="Length of the configured API key (for verification)"
        ),
    },
)

openrouter_api_key_status_response_model = Model(
    "OpenRouterAPIKeyStatusResponse",
    {
        "success": fields.Boolean(default=True, description="Success status"),
        "data": fields.Nested(
            openrouter_api_key_status_model, description="API key status information"
        ),
    },
)

openrouter_api_key_success_model = Model(
    "OpenRouterAPIKeySuccess",
    {
        "message": fields.String(description="Success message"),
    },
)

openrouter_api_key_success_response_model = Model(
    "OpenRouterAPIKeySuccessResponse",
    {
        "success": fields.Boolean(default=True, description="Success status"),
        "data": fields.Nested(
            openrouter_api_key_success_model, description="Success message"
        ),
    },
)

# Response wrapper
response_model = Model(
    "Response",
    {
        "success": fields.Boolean(default=True, description="Success status"),
        "data": fields.Raw(description="Response data"),
        "meta": fields.Raw(description="Additional metadata"),
        "error": fields.Raw(description="Error information, if any"),
    },
)
