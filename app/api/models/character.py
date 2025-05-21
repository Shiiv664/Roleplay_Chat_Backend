"""API models for Character resources."""

from flask_restx import Model, fields

# Character models for request and response serialization
character_model = Model(
    "Character",
    {
        "id": fields.Integer(readOnly=True, description="Character ID"),
        "label": fields.String(
            required=True,
            description="Unique character identifier",
            min_length=1,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="Character name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="Character description"
        ),
        "avatar_image": fields.String(
            required=False, description="Character avatar image path"
        ),
        "avatar_url": fields.String(
            readOnly=True, description="Character avatar image URL"
        ),
        "created_at": fields.DateTime(readOnly=True, description="Creation timestamp"),
        "updated_at": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
    },
)

character_create_model = Model(
    "CharacterCreate",
    {
        "label": fields.String(
            required=True,
            description="Unique character identifier",
            min_length=1,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="Character name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="Character description"
        ),
        "avatar_image": fields.String(
            required=False, description="Character avatar image URL (for JSON requests)"
        ),
    },
)

character_create_multipart_model = Model(
    "CharacterCreateMultipart",
    {
        "label": fields.String(
            required=True,
            description="Unique character identifier",
            min_length=1,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="Character name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="Character description"
        ),
        "avatar_image": fields.Raw(
            required=False,
            description="Character avatar image file (PNG, JPG, GIF, WebP, max 5MB)",
            type="file",
        ),
    },
)

character_update_model = Model(
    "CharacterUpdate",
    {
        "label": fields.String(
            required=False,
            description="Unique character identifier",
            min_length=1,
            max_length=50,
        ),
        "name": fields.String(
            required=False, description="Character name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="Character description"
        ),
        "avatar_image": fields.String(
            required=False, description="Character avatar image path"
        ),
    },
)

# List response model with pagination
character_list_model = Model(
    "CharacterList",
    {
        "items": fields.List(
            fields.Nested(character_model), description="List of characters"
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
