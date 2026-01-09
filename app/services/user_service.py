"""User service."""
from app.models.user import User
from app.extensions import db


class UserService:
    """User service."""

    @staticmethod
    def get_users(page=1, per_page=10):
        """Get paginated list of users."""
        pagination = User.query.filter_by(is_active=True).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError('User not found')
        return user

    @staticmethod
    def update_user(user_id, data):
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ValueError('Email already in use')
            user.email = data['email']

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """Soft delete user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        user.is_active = False
        db.session.commit()
        return user
