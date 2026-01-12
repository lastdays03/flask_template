"""Authentication utilities."""

from flask import current_app
from app.utils.cache import get_redis_client


def check_if_token_in_blocklist(jwt_header, jwt_payload):
    """
    Check if token is revoked.
    Callback for flask-jwt-extended.

    Args:
        jwt_header: JWT header dictionary
        jwt_payload: JWT payload dictionary

    Returns:
        bool: True if token is in blocklist (revoked), False otherwise
    """
    jti = jwt_payload["jti"]
    try:
        r = get_redis_client()
        token_in_redis = r.get(f"blocklist:{jti}")
        return token_in_redis is not None
    except Exception as e:
        current_app.logger.error(f"Error checking blocklist: {e}")
        # Fail safe: if redis is down, assume token is valid
        # (or invalid depending on policy)
        # Here assuming valid to prevent denial of service, but logging error
        return False


def add_token_to_blocklist(jti):
    """
    Add token to blocklist.

    Args:
        jti: Unique identifier of the token
    """
    try:
        r = get_redis_client()
        # Get expiration from config
        expires = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES")
        if expires:
            # Convert timedelta to seconds
            ttl = int(expires.total_seconds())
        else:
            ttl = 3600 * 24 * 30  # 30 days default

        r.setex(f"blocklist:{jti}", ttl, "revoked")
        return True
    except Exception as e:
        current_app.logger.error(f"Error adding token to blocklist: {e}")
        return False
