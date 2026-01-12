"""API versioning utilities."""

from functools import wraps
from flask import request


def api_version_required(min_version="1.0", max_version="2.0"):
    """
    Decorator to enforce API version.

    Usage:
        @api_version_required(min_version='1.0', max_version='2.0')
        def my_endpoint():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get version from header or path
            version = request.headers.get("API-Version")
            if not version:
                if "/api/v2" in request.path:
                    version = "2.0"
                else:
                    version = "1.0"

            try:
                version_float = float(version)
                min_float = float(min_version)
                max_float = float(max_version)

                if version_float < min_float or version_float > max_float:
                    return {
                        "success": False,
                        "error": {
                            "code": "UNSUPPORTED_API_VERSION",
                            "message": f"API version {version} not supported",
                            "supported_versions": f"{min_version} - {max_version}",
                        },
                    }, 400

            except ValueError:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_API_VERSION",
                        "message": f"Invalid API version format: {version}",
                    },
                }, 400

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_api_version():
    """Get API version from request header."""
    return request.headers.get("API-Version", "1.0")


def is_version_compatible(version, target_version):
    """Check if API version is compatible."""
    try:
        return float(version) >= float(target_version)
    except ValueError:
        return False
