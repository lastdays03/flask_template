"""Users API."""
from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required
from app.schemas.user import api, user_model, user_input_model, user_list_model
from app.services.user_service import UserService


@api.route('')
class UserList(Resource):
    """User list resource."""

    @jwt_required()
    @api.marshal_with(user_list_model)
    @api.response(200, 'Success')
    @api.doc(params={
        'page': 'Page number (default: 1)',
        'per_page': 'Items per page (default: 10)'
    })
    def get(self):
        """Get list of users."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        result = UserService.get_users(page=page, per_page=per_page)
        return result, 200


@api.route('/<int:user_id>')
class UserDetail(Resource):
    """User detail resource."""

    @jwt_required()
    @api.marshal_with(user_model)
    @api.response(200, 'Success')
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get user by ID."""
        try:
            user = UserService.get_user_by_id(user_id)
            return user.to_dict(), 200
        except ValueError as e:
            api.abort(404, str(e))

    @jwt_required()
    @api.expect(user_input_model, validate=True)
    @api.marshal_with(user_model)
    @api.response(200, 'User updated')
    @api.response(400, 'Validation error')
    @api.response(404, 'User not found')
    def put(self, user_id):
        """Update user."""
        try:
            user = UserService.update_user(user_id, request.json)
            return user.to_dict(), 200
        except ValueError as e:
            api.abort(400, str(e))

    @jwt_required()
    @api.response(204, 'User deleted')
    @api.response(404, 'User not found')
    def delete(self, user_id):
        """Delete user (soft delete)."""
        try:
            UserService.delete_user(user_id)
            return '', 204
        except ValueError as e:
            api.abort(404, str(e))
