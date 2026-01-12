"""Authentication schemas."""
from flask_restx import fields, Namespace

api = Namespace("auth", description="Authentication operations")

# Request models
login_model = api.model(
    "Login",
    {
        "email": fields.String(
            required=True, description="User email", example="user@example.com"
        ),
        "password": fields.String(
            required=True, description="User password", example="password123"
        ),
    },
)

register_model = api.model(
    "Register",
    {
        "email": fields.String(
            required=True, description="User email", example="user@example.com"
        ),
        "password": fields.String(
            required=True, description="User password", min_length=8
        ),
        "first_name": fields.String(
            required=True, description="First name", example="John"
        ),
        "last_name": fields.String(
            required=True, description="Last name", example="Doe"
        ),
    },
)

refresh_model = api.model(
    "Refresh",
    {"refresh_token": fields.String(required=True, description="Refresh token")},
)

# Response models
token_model = api.model(
    "Token",
    {
        "access_token": fields.String(description="Access token"),
        "refresh_token": fields.String(description="Refresh token"),
        "token_type": fields.String(description="Token type", example="Bearer"),
    },
)

message_model = api.model(
    "Message", {"message": fields.String(description="Response message")}
)
