"""OAuth API endpoints."""

from flask import request, redirect
from flask_restx import Namespace, Resource
from app.services.oauth_service import OAuthService

api = Namespace("oauth", description="OAuth operations")


@api.route("/google/login")
class GoogleLogin(Resource):
    """Google OAuth login."""

    @api.response(302, "Redirect to Google")
    def get(self):
        """Redirect to Google OAuth."""
        auth_url, state = OAuthService.get_google_auth_url()
        return redirect(auth_url)


@api.route("/google/callback")
class GoogleCallback(Resource):
    """Google OAuth callback."""

    @api.response(200, "Login successful")
    @api.response(400, "Invalid authorization code")
    def get(self):
        """Handle Google OAuth callback."""
        code = request.args.get("code")

        if not code:
            api.abort(400, "Authorization code not provided")

        try:
            tokens = OAuthService.handle_google_callback(code)
            return {"success": True, "data": tokens}, 200
        except Exception as e:
            api.abort(500, f"OAuth failed: {str(e)}")
