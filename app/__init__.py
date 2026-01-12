"""Application factory."""

from flask import Flask, jsonify

from app.config import config
from app.extensions import db, migrate, jwt, cors, limiter, celery


def create_app(config_name="default"):
    """Create Flask application."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    jwt.init_app(flask_app)
    cors.init_app(flask_app, origins=flask_app.config["CORS_ORIGINS"])
    limiter.init_app(flask_app)

    # JWT Config
    from app.utils.auth import check_if_token_in_blocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return check_if_token_in_blocklist(jwt_header, jwt_payload)

    # Setup Logging
    from app.utils import setup_logging

    setup_logging(flask_app)

    # Initialize Celery
    celery.conf.update(
        broker_url=flask_app.config["CELERY_BROKER_URL"],
        result_backend=flask_app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Seoul",
        enable_utc=True,
    )

    # Initialize SocketIO
    from app.websocket import socketio

    socketio.init_app(
        flask_app,
        message_queue=flask_app.config["REDIS_URL"],
        async_mode="threading",
    )

    # Import event handlers
    from app.events import notifications  # noqa

    # Initialize Metrics
    if config_name != "testing":
        from app.utils.metrics import init_metrics

        init_metrics(flask_app)

    # Initialize Sentry
    if flask_app.config.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=flask_app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            environment=config_name,
            traces_sample_rate=1.0,
        )

    # Register Middleware
    from app.middleware.version_deprecation import check_version_deprecation

    flask_app.before_request(check_version_deprecation)

    # Register Blueprints (API Versions)
    from app.api.v1 import blueprint as api_v1
    from app.api.v2 import blueprint as api_v2

    flask_app.register_blueprint(api_v1)
    flask_app.register_blueprint(api_v2)

    # API root endpoint
    @flask_app.route("/api")
    def api_root():
        """API version information."""
        return jsonify(
            {
                "name": "Flask REST API",
                "versions": {
                    "v1": {
                        "url": "/api/v1",
                        "docs": "/api/v1/docs",
                        "status": "deprecated",
                    },
                    "v2": {
                        "url": "/api/v2",
                        "docs": "/api/v2/docs",
                        "status": "stable",
                    },
                },
                "default_version": "v2",
                "latest_version": "v2",
            }
        )

    @flask_app.route("/")
    def index():
        return jsonify({"message": "Flask REST API", "documentation": "/api"})

    # Register Error Handlers
    from app.utils.error_handlers import (
        register_error_handlers,
        register_jwt_error_handlers,
    )

    register_error_handlers(flask_app)
    register_jwt_error_handlers(jwt)

    return flask_app
