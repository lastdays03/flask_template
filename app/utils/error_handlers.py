from flask import jsonify
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError


def register_error_handlers(app):
    """Register standard Flask error handlers."""

    @app.errorhandler(NoAuthorizationError)
    def handle_auth_error(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing Authorization Header",
                    },
                }
            ),
            401,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "BAD_REQUEST", "message": str(error)},
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required",
                    },
                }
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "FORBIDDEN", "message": "Access denied"},
                }
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Resource not found"},
                }
            ),
            404,
        )

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                    },
                }
            ),
            429,
        )

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    },
                }
            ),
            500,
        )


def register_jwt_error_handlers(jwt):
    """Register JWT error handlers."""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"},
                }
            ),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid token",
                        "details": str(error),
                    },
                }
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHORIZATION_REQUIRED",
                        "message": "Request does not contain an access token",
                        "details": str(error),
                    },
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "FRESH_TOKEN_REQUIRED",
                        "message": "Fresh token required",
                    },
                }
            ),
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "TOKEN_REVOKED",
                        "message": "Token has been revoked",
                    },
                }
            ),
            401,
        )


def register_api_error_handlers(api):
    """Register Flask-RestX API error handlers."""

    @api.errorhandler(NoAuthorizationError)
    def handle_auth_error(error):
        return {
            "success": False,
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Missing Authorization Header",
            },
        }, 401

    @api.errorhandler(ExpiredSignatureError)
    def handle_expired_error(error):
        return {
            "success": False,
            "error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"},
        }, 401
