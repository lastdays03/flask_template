"""Authentication service."""
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models.user import User
from app.extensions import db


class AuthService:
    """Authentication service."""

    @staticmethod
    def register_user(email, password, first_name, last_name):
        """Register a new user."""
        # Check if user exists
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')

        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()

        return user

    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user and return user object."""
        user = User.query.filter_by(email=email, is_active=True).first()

        if not user or not user.check_password(password):
            raise ValueError('Invalid email or password')

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        return user

    @staticmethod
    def create_tokens(user_id):
        """Create access and refresh tokens."""
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
