"""Authentication API."""

from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.schemas.auth import (
    api,
    login_model,
    register_model,
    token_model,
)
from app.services.auth_service import AuthService
from app.extensions import limiter
from app.models.user import User


@api.route("/register")
class Register(Resource):
    """User registration."""

    @api.expect(register_model, validate=True)
    @api.response(201, "User registered successfully")
    @api.response(400, "Validation error")
    @limiter.limit("5 per minute")
    def post(self):
        """Register a new user."""
        data = request.json

        try:
            user = AuthService.register_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            return {
                "success": True,
                "message": "User registered successfully",
                "data": user.to_dict(),
            }, 201

        except ValueError as e:
            api.abort(400, str(e))
        except Exception:
            api.abort(500, "Registration failed")


@api.route("/login")
class Login(Resource):
    """User login."""

    @api.expect(login_model, validate=True)
    @api.marshal_with(token_model)
    @api.response(200, "Login successful")
    @api.response(401, "Invalid credentials")
    @limiter.limit("5 per minute")
    def post(self):
        """Login and get tokens."""
        data = request.json

        try:
            user = AuthService.authenticate_user(
                email=data["email"], password=data["password"]
            )

            tokens = AuthService.create_tokens(user.id)
            return tokens, 200

        except ValueError as e:
            api.abort(401, str(e))
        except Exception:
            api.abort(500, "Login failed")


@api.route("/refresh")
class Refresh(Resource):
    """Token refresh."""

    @jwt_required(refresh=True)
    @api.marshal_with(token_model)
    @api.response(200, "Token refreshed")
    @limiter.limit("10 per minute")
    def post(self):
        """Refresh access token."""
        user_id = get_jwt_identity()
        tokens = AuthService.create_tokens(user_id)
        return {"access_token": tokens["access_token"]}, 200


@api.route("/me")
class Me(Resource):
    """Current user info."""

    @jwt_required()
    @api.response(200, "Success")
    @api.response(401, "Unauthorized")
    def get(self):
        """Get current user information."""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            api.abort(404, "User not found")

        return {"success": True, "data": user.to_dict()}, 200


@api.route("/logout")
class Logout(Resource):
    """User logout."""

    @jwt_required()
    @api.response(200, "Logout successful")
    def post(self):
        """Logout user."""
        jti = get_jwt()["jti"]
        AuthService.logout_user(jti)
        return {"success": True, "message": "Logout successful"}, 200
