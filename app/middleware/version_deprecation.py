"""API version deprecation middleware."""
from flask import request, g
import warnings


def check_version_deprecation():
    """Check for deprecated API versions."""
    version = request.headers.get('API-Version', '1.0')

    # Warn about old versions
    if version < '2.0':
        warnings.warn(
            f'API version {version} is deprecated and will be removed',
            DeprecationWarning
        )
        g.deprecated_version = True
