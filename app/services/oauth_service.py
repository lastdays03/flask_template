"""OAuth service."""

from authlib.integrations.requests_client import OAuth2Session
from flask import current_app
from app.models.user import User
from app.services.auth_service import AuthService


class OAuthService:
    """OAuth service for social login."""

    @staticmethod
    def get_google_oauth_session():
        """Get Google OAuth2 session."""
        return OAuth2Session(
            client_id=current_app.config["GOOGLE_CLIENT_ID"],
            client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
            redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
            scope="openid email profile",
        )

    @staticmethod
    def get_google_auth_url():
        """Get Google authorization URL."""
        session = OAuthService.get_google_oauth_session()
        authorization_url, state = session.create_authorization_url(
            "https://accounts.google.com/o/oauth2/v2/auth"
        )
        return authorization_url, state

    @staticmethod
    def handle_google_callback(code):
        """Handle Google OAuth callback."""
        session = OAuthService.get_google_oauth_session()

        # Exchange code for token
        _token = session.fetch_token("https://oauth2.googleapis.com/token", code=code)

        # Get user info
        resp = session.get("https://www.googleapis.com/oauth2/v1/userinfo")
        user_info = resp.json()

        # Find or create user
        user = User.query.filter_by(email=user_info["email"]).first()

        if not user:
            # Create new user from OAuth
            user = User(
                email=user_info["email"],
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                password_hash="oauth_user",  # No password for OAuth users
                is_active=True,
            )
            user.save()

        # Create JWT tokens
        return AuthService.create_tokens(user.id)
