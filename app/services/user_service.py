"""User service module."""
from app.models.user import User
from app.extensions import db
from app.utils.cache import cached, invalidate_cache


class UserService:
    """User service."""

    @staticmethod
    @cached(ttl=60, key_prefix="user_list")
    def get_users(page=1, per_page=10):
        """
        Get paginated list of users.

        Returns pagination object.
        """
        from app.utils.pagination import Pagination

        pagination = User.query.filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Detach items from session to make them pickleable
        items = pagination.items
        for item in items:
            db.session.expunge(item)

        return Pagination(
            items=items,
            page=pagination.page,
            per_page=pagination.per_page,
            total=pagination.total,
        )

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found")
        return user

    @staticmethod
    def update_user(user_id, data):
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]

        # Check email uniqueness if email is being updated
        if "email" in data and data["email"] != user.email:
            existing = User.query.filter_by(email=data["email"]).first()
            if existing:
                raise ValueError("Email already in use")
            user.email = data["email"]

        if "password" in data:
            user.set_password(data["password"])

        db.session.commit()

        # Invalidate cache
        invalidate_cache("user_list:*")

        return user

    @staticmethod
    def delete_user(user_id):
        """Soft delete user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        user.is_active = False
        db.session.commit()

        # Invalidate cache
        invalidate_cache("user_list:*")

        return user
