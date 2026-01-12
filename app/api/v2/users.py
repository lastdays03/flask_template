"""Users API v2."""

from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required
from app.services.user_service import UserService
from app.utils.versioning import api_version_required

api = Namespace("users", description="Users operations (v2)")


@api.route("")
class UserListV2(Resource):
    """User list resource (v2)."""

    @jwt_required()
    @api_version_required(min_version="2.0")
    @api.doc(
        params={
            "page": {"description": "Page number", "type": "integer", "default": 1},
            "per_page": {
                "description": "Items per page",
                "type": "integer",
                "default": 10,
            },
            "API-Version": {
                "in": "header",
                "description": "API Version",
                "default": "2.0",
                "required": False,
            },
        }
    )
    @api.response(200, "Success")
    def get(self):
        """
        Get list of users (v2).

        Includes metadata and enhanced response structure.
        """
        import time
        from flask import jsonify, make_response
        from app.utils.pagination import generate_pagination_links, paginate_response

        start_time = time.time()

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        # Validate page number
        page = max(page, 1)
        if per_page < 1:
            per_page = 10

        pagination = UserService.get_users(page=page, per_page=per_page)
        users = [user.to_dict() for user in pagination.items]

        # Use utility to structure the response data
        response_data = paginate_response(
            pagination, users, "api_v2.users_user_list_v2", per_page=per_page
        )

        # Add additional metadata for v2
        response_data["success"] = True
        response_data["metadata"] = {
            "version": "2.0",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        # Generate Link header (RFC 5988)
        link_header = generate_pagination_links(
            pagination, "api_v2.users_user_list_v2", per_page=per_page
        )

        # Prepare headers
        headers = {
            "Link": link_header,
            "X-Total-Count": str(pagination.total),
            "X-Page": str(pagination.page),
            "X-Per-Page": str(pagination.per_page),
            "X-Total-Pages": str(pagination.pages),
        }

        return response_data, 200, headers
