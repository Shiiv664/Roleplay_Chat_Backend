"""API models for ChatSession resources."""

from flask_restx import Model, fields

# ChatSession models for request and response serialization
chat_session_model = Model(
    "ChatSession",
    {
        "id": fields.Integer(readOnly=True, description="Chat Session ID"),
        "character_id": fields.Integer(
            required=True, description="Character ID for this session"
        ),
        "user_profile_id": fields.Integer(
            required=True, description="User Profile ID for this session"
        ),
        "ai_model_id": fields.Integer(
            required=True, description="AI Model ID for this session"
        ),
        "system_prompt_id": fields.Integer(
            required=True, description="System Prompt ID for this session"
        ),
        "pre_prompt": fields.String(
            required=False, description="Optional text to add before each AI request"
        ),
        "pre_prompt_enabled": fields.Boolean(
            required=True, description="Whether pre-prompt is enabled", default=False
        ),
        "post_prompt": fields.String(
            required=False, description="Optional text to add after each AI request"
        ),
        "post_prompt_enabled": fields.Boolean(
            required=True, description="Whether post-prompt is enabled", default=False
        ),
        "start_time": fields.DateTime(
            readOnly=True, description="Session start timestamp"
        ),
        "updated_at": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
        "message_count": fields.Integer(
            readOnly=True, description="Number of messages in this session"
        ),
    },
)

chat_session_create_model = Model(
    "ChatSessionCreate",
    {
        "character_id": fields.Integer(
            required=True, description="Character ID for this session"
        ),
    },
)

chat_session_update_model = Model(
    "ChatSessionUpdate",
    {
        "ai_model_id": fields.Integer(
            required=False, description="AI Model ID for this session"
        ),
        "system_prompt_id": fields.Integer(
            required=False, description="System Prompt ID for this session"
        ),
        "pre_prompt": fields.String(
            required=False, description="Optional text to add before each AI request"
        ),
        "pre_prompt_enabled": fields.Boolean(
            required=False, description="Whether pre-prompt is enabled"
        ),
        "post_prompt": fields.String(
            required=False, description="Optional text to add after each AI request"
        ),
        "post_prompt_enabled": fields.Boolean(
            required=False, description="Whether post-prompt is enabled"
        ),
    },
)

# List response model with pagination
chat_session_list_model = Model(
    "ChatSessionList",
    {
        "items": fields.List(
            fields.Nested(chat_session_model), description="List of chat sessions"
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
