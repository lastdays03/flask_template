"""Application factory."""
import logging
from flask import Flask, jsonify
from flask_restx import Api

from app.config import config
from app.extensions import db, migrate, jwt, cors, limiter, celery


def create_app(config_name='default'):
    """Create Flask application."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    jwt.init_app(flask_app)
    cors.init_app(flask_app, origins=flask_app.config['CORS_ORIGINS'])
    limiter.init_app(flask_app)

    # Setup Logging
    from app.utils import setup_logging
    setup_logging(flask_app)

    # Initialize Celery
    celery.conf.update(
        broker_url=flask_app.config['CELERY_BROKER_URL'],
        result_backend=flask_app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Asia/Seoul',
        enable_utc=True,
    )

    # Initialize SocketIO
    from app.websocket import socketio
    socketio.init_app(
        flask_app,
        message_queue=flask_app.config['REDIS_URL'],
        async_mode='threading'
    )

    # Import event handlers
    import app.events.notifications

    # Create Flask-RESTX API
    api = Api(
        flask_app,
        version='1.0',
        title='Flask REST API',
        description='Production-ready Flask REST API Template',
        doc='/api/docs'
    )

    # Register error handlers
    register_error_handlers(flask_app)

    # Register blueprints
    # Import API implementations to register resources with namespaces
    import app.api.auth
    import app.api.users

    from app.api import health_ns
    from app.schemas.auth import api as auth_ns
    from app.schemas.user import api as users_ns
    from app.api import oauth_ns
    
    api.add_namespace(health_ns, path='/api/health')
    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(users_ns, path='/api/users')
    api.add_namespace(oauth_ns, path='/api/oauth')

    return flask_app


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(error)
            }
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Access denied'
            }
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Too many requests'
            }
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal error: {error}')
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }), 500
