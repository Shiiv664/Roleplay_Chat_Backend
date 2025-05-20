"""API models for AIModel resources."""

from flask_restx import Model, fields

# AIModel models for request and response serialization
ai_model_model = Model(
    "AIModel",
    {
        "id": fields.Integer(readOnly=True, description="AI Model ID"),
        "label": fields.String(
            required=True,
            description="Unique AI model identifier",
            min_length=2,
            max_length=50,
        ),
        "description": fields.String(
            required=False, description="AI model description"
        ),
        "created_at": fields.DateTime(readOnly=True, description="Creation timestamp"),
        "updated_at": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
    },
)

# Short version for nested references
ai_model_short_model = Model(
    "AIModelShort",
    {
        "id": fields.Integer(readOnly=True, description="AI Model ID"),
        "label": fields.String(description="Unique AI model identifier"),
        "description": fields.String(description="AI model description"),
    },
)

ai_model_create_model = Model(
    "AIModelCreate",
    {
        "label": fields.String(
            required=True,
            description="Unique AI model identifier",
            min_length=2,
            max_length=50,
        ),
        "description": fields.String(
            required=False, description="AI model description"
        ),
    },
)

ai_model_update_model = Model(
    "AIModelUpdate",
    {
        "label": fields.String(
            required=False,
            description="Unique AI model identifier",
            min_length=2,
            max_length=50,
        ),
        "description": fields.String(
            required=False, description="AI model description"
        ),
    },
)

# List response model with pagination
ai_model_list_model = Model(
    "AIModelList",
    {
        "items": fields.List(
            fields.Nested(ai_model_model), description="List of AI models"
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
