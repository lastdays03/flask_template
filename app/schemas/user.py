"""User schemas."""

from flask_restx import fields, Namespace

api = Namespace("users", description="User operations")

# User model
user_model = api.model(
    "User",
    {
        "id": fields.Integer(readonly=True, description="User ID"),
        "email": fields.String(required=True, description="User email"),
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "is_active": fields.Boolean(description="User active status"),
        "last_login": fields.DateTime(description="Last login timestamp"),
        "created_at": fields.DateTime(readonly=True, description="Creation timestamp"),
        "updated_at": fields.DateTime(
            readonly=True, description="Last update timestamp"
        ),
    },
)

# User input model (for updates)
user_input_model = api.model(
    "UserInput",
    {
        "first_name": fields.String(description="First name"),
        "last_name": fields.String(description="Last name"),
        "email": fields.String(description="Email"),
    },
)

# User list model
user_list_model = api.model(
    "UserList",
    {
        "users": fields.List(fields.Nested(user_model)),
        "total": fields.Integer(description="Total count"),
        "page": fields.Integer(description="Current page"),
        "per_page": fields.Integer(description="Items per page"),
        "pages": fields.Integer(description="Total pages"),
    },
)
