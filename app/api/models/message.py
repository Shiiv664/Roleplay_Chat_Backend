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

# Request model for sending messages
send_message_model = Model(
    "SendMessage",
    {
        "content": fields.String(
            required=True,
            description="The message content to send",
            example="Hello, can you help me understand quantum physics?",
        ),
        "stream": fields.Boolean(
            required=False,
            default=True,
            description="Whether to stream the AI response. If true, returns SSE stream. If false, returns complete response (not implemented yet).",
            example=True,
        ),
    },
)

# Response model for streaming events
stream_event_model = Model(
    "StreamEvent",
    {
        "type": fields.String(
            required=True,
            description="Event type",
            enum=["content", "error", "done"],
            example="content",
        ),
        "data": fields.String(
            required=False,
            description="Event data (chunk of response text for content events)",
            example="Quantum physics is",
        ),
        "error": fields.String(
            required=False,
            description="Error message (only for error events)",
            example="OpenRouter API rate limit exceeded",
        ),
    },
)

# Response model for non-streaming mode (future)
send_message_response_model = Model(
    "SendMessageResponse",
    {
        "user_message": fields.Nested(
            message_model, description="The created user message"
        ),
        "ai_response": fields.Nested(
            message_model, description="The generated AI response"
        ),
    },
)

# Error response model
send_message_error_model = Model(
    "SendMessageError",
    {
        "success": fields.Boolean(default=False, description="Always false for errors"),
        "error": fields.String(description="Error type", example="VALIDATION_ERROR"),
        "message": fields.String(
            description="Human-readable error message",
            example="Message content is required",
        ),
        "details": fields.Raw(description="Additional error details", required=False),
    },
)
