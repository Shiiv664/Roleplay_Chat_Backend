"""API models for Message resources."""

from flask_restx import Model, fields

# Basic message model for responses
message_model = Model(
    "Message",
    {
        "id": fields.Integer(readOnly=True, description="Message ID"),
        "chat_session_id": fields.Integer(required=True, description="Chat Session ID"),
        "role": fields.String(
            required=True,
            description="Message role (user or assistant)",
            enum=["user", "assistant"],
        ),
        "content": fields.String(required=True, description="Message content"),
        "timestamp": fields.DateTime(readOnly=True, description="Message timestamp"),
    },
)

# Model for creating a new message
message_create_model = Model(
    "MessageCreate",
    {
        "role": fields.String(
            required=True,
            description="Message role (user or assistant)",
            enum=["user", "assistant"],
        ),
        "content": fields.String(required=True, description="Message content"),
    },
)

# Model for creating a user message with AI response
user_message_create_model = Model(
    "UserMessageCreate",
    {"content": fields.String(required=True, description="User message content")},
)

# Model for updating a message
message_update_model = Model(
    "MessageUpdate",
    {"content": fields.String(required=True, description="Updated message content")},
)

# Model for response with both user and AI messages
message_with_response_model = Model(
    "MessageWithResponse",
    {
        "user_message": fields.Nested(message_model, description="User message"),
        "ai_message": fields.Nested(message_model, description="AI response"),
    },
)

# List response model with pagination
message_list_model = Model(
    "MessageList",
    {
        "items": fields.List(
            fields.Nested(message_model), description="List of messages"
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
