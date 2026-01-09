"""Application factory."""
import logging
from flask import Flask, jsonify
from flask_restx import Api

from app.config import config
from app.extensions import db, migrate, jwt, cors, limiter, celery


def create_app(config_name='default'):
    """Create Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    limiter.init_app(app)

    # Setup Logging
    from app.utils import setup_logging
    setup_logging(app)

    # Initialize Celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Asia/Seoul',
        enable_utc=True,
    )

    # Create Flask-RESTX API
    api = Api(
        app,
        version='1.0',
        title='Flask REST API',
        description='Production-ready Flask REST API Template',
        doc='/api/docs'
    )

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints (will add later)
    from app.api import health_ns
    api.add_namespace(health_ns, path='/api/health')
    # from app.api import auth_ns, users_ns
    # api.add_namespace(auth_ns, path='/api/auth')
    # api.add_namespace(users_ns, path='/api/users')

    return app


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
