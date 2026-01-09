"""Users API v2."""
from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required
from app.services.user_service import UserService
from app.utils.versioning import api_version_required

api = Namespace('users', description='Users operations (v2)')


@api.route('')
class UserListV2(Resource):
    """User list resource (v2)."""

    @jwt_required()
    @api_version_required(min_version='2.0')
    @api.response(200, 'Success')
    def get(self):
        """
        Get list of users (v2).
        
        Includes metadata and enhanced response structure.
        """
        import time
        start_time = time.time()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        result = UserService.get_users(page=page, per_page=per_page)

        return {
            'success': True,
            'data': result['users'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'pages': result['pages']
            },
            'metadata': {
                'version': '2.0',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        }, 200
