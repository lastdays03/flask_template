"""Users API."""
from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required
from app.schemas.user import api, user_model, user_input_model, user_list_model
from app.services.user_service import UserService


from app.utils.pagination import generate_pagination_links, paginate_response

@api.route('')
class UserList(Resource):
    """User list resource."""

    @jwt_required()
    @api.doc(params={
        'page': {'description': 'Page number', 'type': 'integer', 'default': 1},
        'per_page': {'description': 'Items per page', 'type': 'integer', 'default': 10}
    })
    def get(self):
        """Get list of users with Link headers."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Validate pagination parameters
        if page < 1:
            api.abort(400, 'Page must be >= 1')
        if per_page < 1 or per_page > 100:
            api.abort(400, 'Per page must be between 1 and 100')

        pagination = UserService.get_users(page=page, per_page=per_page)
        users_data = [user.to_dict() for user in pagination.items]

        # Create HATEOAS response
        response_data = paginate_response(
            pagination,
            users_data,
            'api_v1.users_user_list',
            per_page=per_page
        )
        
        # For v1 backward compatibility, we simplify the response structure slightly if needed,
        # but here we follow the HATEOAS structure as an enhancement.
        # Alternatively, to keep strictly v1 format but add headers:
        
        response_body = {
            'users': users_data,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'links': response_data['links'] # Add links to body
        }

        response = make_response(jsonify(response_body), 200)

        # Add Link header (RFC 5988)
        link_header = generate_pagination_links(
            pagination,
            'api_v1.users_user_list',
            per_page=per_page
        )
        response.headers['Link'] = link_header

        # Add custom pagination headers
        response.headers['X-Total-Count'] = str(pagination.total)
        response.headers['X-Page'] = str(pagination.page)
        response.headers['X-Per-Page'] = str(pagination.per_page)
        response.headers['X-Total-Pages'] = str(pagination.pages)

        return response


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
