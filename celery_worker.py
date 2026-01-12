"""Celery worker entry point."""

import os
from app import create_app
from app.extensions import celery

# Create Flask app and push context
app = create_app(os.getenv("FLASK_ENV", "development"))
app.app_context().push()
