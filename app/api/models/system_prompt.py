"""API models for SystemPrompt resources."""

from flask_restx import Model, fields

# SystemPrompt models for request and response serialization
system_prompt_model = Model(
    "SystemPrompt",
    {
        "id": fields.Integer(readOnly=True, description="System Prompt ID"),
        "label": fields.String(
            required=True,
            description="Unique system prompt identifier",
            min_length=2,
            max_length=50,
        ),
        "content": fields.String(
            required=True, description="System prompt content", min_length=1
        ),
        "created_at": fields.DateTime(readOnly=True, description="Creation timestamp"),
        "updated_at": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
    },
)

# Short version for nested references
system_prompt_short_model = Model(
    "SystemPromptShort",
    {
        "id": fields.Integer(readOnly=True, description="System Prompt ID"),
        "label": fields.String(description="Unique system prompt identifier"),
        "content": fields.String(description="System prompt content"),
    },
)

system_prompt_create_model = Model(
    "SystemPromptCreate",
    {
        "label": fields.String(
            required=True,
            description="Unique system prompt identifier",
            min_length=2,
            max_length=50,
        ),
        "content": fields.String(
            required=True, description="System prompt content", min_length=1
        ),
    },
)

system_prompt_update_model = Model(
    "SystemPromptUpdate",
    {
        "label": fields.String(
            required=False,
            description="Unique system prompt identifier",
            min_length=2,
            max_length=50,
        ),
        "content": fields.String(
            required=False, description="System prompt content", min_length=1
        ),
    },
)

# List response model with pagination
system_prompt_list_model = Model(
    "SystemPromptList",
    {
        "items": fields.List(
            fields.Nested(system_prompt_model), description="List of system prompts"
        ),
        "pagination": fields.Raw(description="Pagination information"),
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
