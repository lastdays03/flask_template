"""API package."""
from app.api.health import api as health_ns
from app.schemas.auth import api as auth_ns

__all__ = ['health_ns', 'auth_ns']
