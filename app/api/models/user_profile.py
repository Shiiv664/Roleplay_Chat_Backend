"""API models for UserProfile resources."""

from flask_restx import Model, fields

# UserProfile models for request and response serialization
user_profile_model = Model(
    "UserProfile",
    {
        "id": fields.Integer(readOnly=True, description="User Profile ID"),
        "label": fields.String(
            required=True,
            description="Unique user profile identifier",
            min_length=2,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="User profile name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="User profile description"
        ),
        "avatar_image": fields.String(
            required=False, description="User profile avatar image path"
        ),
        "avatar_url": fields.String(
            readOnly=True, description="Full URL to the user profile avatar image"
        ),
        "created_at": fields.DateTime(readOnly=True, description="Creation timestamp"),
        "updated_at": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
    },
)

# Short version for nested references
user_profile_short_model = Model(
    "UserProfileShort",
    {
        "id": fields.Integer(readOnly=True, description="User Profile ID"),
        "label": fields.String(description="Unique user profile identifier"),
        "name": fields.String(description="User profile name"),
        "avatar_image": fields.String(description="User profile avatar image path"),
        "avatar_url": fields.String(
            description="Full URL to the user profile avatar image"
        ),
    },
)

user_profile_create_model = Model(
    "UserProfileCreate",
    {
        "label": fields.String(
            required=True,
            description="Unique user profile identifier",
            min_length=2,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="User profile name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="User profile description"
        ),
        "avatar_image": fields.String(
            required=False, description="User profile avatar image path"
        ),
    },
)

user_profile_create_multipart_model = Model(
    "UserProfileCreateMultipart",
    {
        "label": fields.String(
            required=True,
            description="Unique user profile identifier",
            min_length=2,
            max_length=50,
        ),
        "name": fields.String(
            required=True, description="User profile name", min_length=1, max_length=100
        ),
        "description": fields.String(
            required=False, description="User profile description"
        ),
        "avatar_image": fields.Raw(
            required=False,
            description="User profile avatar image file (PNG, JPG, GIF, WebP, max 5MB, max 1024x1024px)",
        ),
    },
)

user_profile_update_model = Model(
    "UserProfileUpdate",
    {
        "label": fields.String(
            required=False,
            description="Unique user profile identifier",
            min_length=2,
            max_length=50,
        ),
        "name": fields.String(
            required=False,
            description="User profile name",
            min_length=1,
            max_length=100,
        ),
        "description": fields.String(
            required=False, description="User profile description"
        ),
        "avatar_image": fields.String(
            required=False, description="User profile avatar image path"
        ),
    },
)

# List response model with pagination
user_profile_list_model = Model(
    "UserProfileList",
    {
        "items": fields.List(
            fields.Nested(user_profile_model), description="List of user profiles"
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
