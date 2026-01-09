# Flask Production REST API Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build production-ready Flask REST API backend template with JWT auth, Celery async tasks, Docker deployment

**Architecture:** Blueprint-based modular structure with Application Factory pattern. Services layer for business logic, Flask-RESTX for API documentation, SQLAlchemy ORM with MySQL, Celery + Redis for async tasks

**Tech Stack:** Flask 3.x, Flask-RESTX, SQLAlchemy, JWT, MySQL, Redis, Celery, Docker, pytest

---

## Task 1: Project Initial Setup

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `.dockerignore`

**Step 1: Create requirements.txt**

Create file with production dependencies:

```txt
Flask==3.0.3
flask-restx==1.3.0
flask-sqlalchemy==3.1.1
flask-migrate==4.0.7
flask-jwt-extended==4.6.0
flask-cors==4.0.1
flask-limiter==3.5.1
PyMySQL==1.1.1
cryptography==42.0.5
redis==5.0.3
celery==5.3.6
gunicorn==21.2.0
python-dotenv==1.0.1
python-json-logger==2.0.7
passlib==1.7.4
bcrypt==4.1.3
```

**Step 2: Create requirements-dev.txt**

Create file with development dependencies:

```txt
-r requirements.txt
pytest==7.4.4
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==23.3.0
black==24.3.0
flake8==7.0.0
```

**Step 3: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Environment
.env
.flaskenv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# Test
.pytest_cache/
.coverage
htmlcov/

# Docker
.DS_Store
```

**Step 4: Create .dockerignore**

```dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.env
.git
.gitignore
.dockerignore
README.md
.pytest_cache
.coverage
htmlcov
*.log
logs/
.DS_Store
```

**Step 5: Commit**

```bash
git add requirements.txt requirements-dev.txt .gitignore .dockerignore
git commit -m "chore: add project dependencies and ignore files"
```

---

## Task 2: Application Configuration

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/extensions.py`

**Step 1: Create app/extensions.py**

Initialize Flask extensions:

```python
"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
celery = Celery()
```

**Step 2: Create app/config.py**

Define configuration classes:

```python
"""Application configuration."""
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/2')


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost:3306/flask_dev'
    )


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # Production security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

**Step 3: Create app/__init__.py (Application Factory)**

```python
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
    # from app.api import health_ns, auth_ns, users_ns
    # api.add_namespace(health_ns, path='/api/health')
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
```

**Step 4: Commit**

```bash
git add app/__init__.py app/config.py app/extensions.py
git commit -m "feat: add application factory and configuration"
```

---

## Task 3: Database Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/base.py`
- Create: `app/models/user.py`

**Step 1: Create app/models/base.py**

```python
"""Base model with common fields."""
from datetime import datetime
from app.extensions import db


class BaseModel(db.Model):
    """Base model class with common fields."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def save(self):
        """Save the model to database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the model from database."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

**Step 2: Create app/models/user.py**

```python
"""User model."""
from datetime import datetime
from passlib.hash import bcrypt
from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = 'users'

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        """Check if password matches hash."""
        return bcrypt.verify(password, self.password_hash)

    def to_dict(self):
        """Convert user to dictionary."""
        data = super().to_dict()
        data.update({
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        })
        return data

    def __repr__(self):
        return f'<User {self.email}>'
```

**Step 3: Create app/models/__init__.py**

```python
"""Models package."""
from app.models.base import BaseModel
from app.models.user import User

__all__ = ['BaseModel', 'User']
```

**Step 4: Commit**

```bash
git add app/models/
git commit -m "feat: add database models (base and user)"
```

---

## Task 4: Logging Utilities

**Files:**
- Create: `app/utils/__init__.py`
- Create: `app/utils/logger.py`

**Step 1: Create app/utils/logger.py**

```python
"""Logging configuration."""
import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logging(app):
    """Set up application logging."""

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'levelname': 'level', 'asctime': 'timestamp'}
    )

    # File handler for all logs
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)

    # File handler for errors
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)

    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)

    # Log startup
    app.logger.info('Flask application started')
```

**Step 2: Create app/utils/__init__.py**

```python
"""Utilities package."""
from app.utils.logger import setup_logging

__all__ = ['setup_logging']
```

**Step 3: Update app/__init__.py to use logging**

Add after creating app:

```python
# In create_app function, add before return:
from app.utils import setup_logging
setup_logging(app)
```

**Step 4: Commit**

```bash
git add app/utils/
git commit -m "feat: add JSON logging utilities"
```

---

## Task 5: Health Check API

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/health.py`

**Step 1: Create app/api/health.py**

```python
"""Health check API."""
from datetime import datetime
from flask import current_app
from flask_restx import Namespace, Resource
from app.extensions import db
import redis

api = Namespace('health', description='Health check operations')


@api.route('')
class HealthCheck(Resource):
    """Health check resource."""

    def get(self):
        """Check service health."""
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {},
            'version': '1.0.0'
        }

        # Check database
        try:
            db.session.execute('SELECT 1')
            status['services']['database'] = 'ok'
        except Exception as e:
            status['services']['database'] = 'error'
            status['status'] = 'unhealthy'
            current_app.logger.error(f'Database health check failed: {e}')

        # Check Redis
        try:
            r = redis.from_url(current_app.config['REDIS_URL'])
            r.ping()
            status['services']['redis'] = 'ok'
        except Exception as e:
            status['services']['redis'] = 'error'
            status['status'] = 'unhealthy'
            current_app.logger.error(f'Redis health check failed: {e}')

        # Check Celery (basic check)
        try:
            from app.extensions import celery
            inspect = celery.control.inspect()
            if inspect.active() is not None:
                status['services']['celery'] = 'ok'
            else:
                status['services']['celery'] = 'no workers'
        except Exception as e:
            status['services']['celery'] = 'error'
            current_app.logger.error(f'Celery health check failed: {e}')

        return status, 200 if status['status'] == 'healthy' else 503
```

**Step 2: Create app/api/__init__.py**

```python
"""API package."""
from app.api.health import api as health_ns

__all__ = ['health_ns']
```

**Step 3: Update app/__init__.py to register health namespace**

Uncomment and update the blueprint registration section:

```python
# Register namespaces
from app.api import health_ns
api.add_namespace(health_ns, path='/api/health')
```

**Step 4: Commit**

```bash
git add app/api/
git commit -m "feat: add health check endpoint"
```

---

## Task 6: Entry Points

**Files:**
- Create: `wsgi.py`
- Create: `.env.example`
- Create: `.flaskenv`

**Step 1: Create wsgi.py**

```python
"""WSGI entry point for production."""
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()
```

**Step 2: Create .env.example**

```bash
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/flask_app

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/2

# Logging
LOG_LEVEL=INFO
```

**Step 3: Create .flaskenv**

```bash
FLASK_APP=wsgi.py
FLASK_DEBUG=1
```

**Step 4: Test basic app startup**

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Try running the app
flask run
```

Expected: Flask dev server starts (may error on DB connection, that's OK for now)

**Step 5: Commit**

```bash
git add wsgi.py .env.example .flaskenv
git commit -m "feat: add WSGI entry point and environment config"
```

---

## Task 7: Authentication Schemas

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/auth.py`
- Create: `app/schemas/user.py`

**Step 1: Create app/schemas/auth.py**

```python
"""Authentication schemas."""
from flask_restx import fields, Namespace

api = Namespace('auth', description='Authentication operations')

# Request models
login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email', example='user@example.com'),
    'password': fields.String(required=True, description='User password', example='password123')
})

register_model = api.model('Register', {
    'email': fields.String(required=True, description='User email', example='user@example.com'),
    'password': fields.String(required=True, description='User password', min_length=8),
    'first_name': fields.String(required=True, description='First name', example='John'),
    'last_name': fields.String(required=True, description='Last name', example='Doe')
})

refresh_model = api.model('Refresh', {
    'refresh_token': fields.String(required=True, description='Refresh token')
})

# Response models
token_model = api.model('Token', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token'),
    'token_type': fields.String(description='Token type', example='Bearer')
})

message_model = api.model('Message', {
    'message': fields.String(description='Response message')
})
```

**Step 2: Create app/schemas/user.py**

```python
"""User schemas."""
from flask_restx import fields, Namespace

api = Namespace('users', description='User operations')

# User model
user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='User ID'),
    'email': fields.String(required=True, description='User email'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'is_active': fields.Boolean(description='User active status'),
    'last_login': fields.DateTime(description='Last login timestamp'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp')
})

# User input model (for updates)
user_input_model = api.model('UserInput', {
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'email': fields.String(description='Email')
})

# User list model
user_list_model = api.model('UserList', {
    'users': fields.List(fields.Nested(user_model)),
    'total': fields.Integer(description='Total count'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'pages': fields.Integer(description='Total pages')
})
```

**Step 3: Create app/schemas/__init__.py**

```python
"""Schemas package."""
from app.schemas.auth import api as auth_api, login_model, register_model, token_model
from app.schemas.user import api as user_api, user_model, user_input_model, user_list_model

__all__ = [
    'auth_api',
    'user_api',
    'login_model',
    'register_model',
    'token_model',
    'user_model',
    'user_input_model',
    'user_list_model'
]
```

**Step 4: Commit**

```bash
git add app/schemas/
git commit -m "feat: add Flask-RESTX schemas for auth and users"
```

---

## Task 8: Authentication Service

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/auth_service.py`

**Step 1: Create app/services/auth_service.py**

```python
"""Authentication service."""
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models.user import User
from app.extensions import db


class AuthService:
    """Authentication service."""

    @staticmethod
    def register_user(email, password, first_name, last_name):
        """Register a new user."""
        # Check if user exists
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')

        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()

        return user

    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user and return user object."""
        user = User.query.filter_by(email=email, is_active=True).first()

        if not user or not user.check_password(password):
            raise ValueError('Invalid email or password')

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        return user

    @staticmethod
    def create_tokens(user_id):
        """Create access and refresh tokens."""
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
```

**Step 2: Create app/services/__init__.py**

```python
"""Services package."""
from app.services.auth_service import AuthService

__all__ = ['AuthService']
```

**Step 3: Commit**

```bash
git add app/services/
git commit -m "feat: add authentication service"
```

---

## Task 9: Authentication API

**Files:**
- Create: `app/api/auth.py`
- Modify: `app/api/__init__.py`
- Modify: `app/__init__.py`

**Step 1: Create app/api/auth.py**

```python
"""Authentication API."""
from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.schemas.auth import api, login_model, register_model, token_model, message_model
from app.services.auth_service import AuthService
from app.extensions import limiter
from app.models.user import User


@api.route('/register')
class Register(Resource):
    """User registration."""

    @api.expect(register_model, validate=True)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Validation error')
    @limiter.limit("5 per minute")
    def post(self):
        """Register a new user."""
        data = request.json

        try:
            user = AuthService.register_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )

            return {
                'success': True,
                'message': 'User registered successfully',
                'data': user.to_dict()
            }, 201

        except ValueError as e:
            api.abort(400, str(e))
        except Exception as e:
            api.abort(500, 'Registration failed')


@api.route('/login')
class Login(Resource):
    """User login."""

    @api.expect(login_model, validate=True)
    @api.marshal_with(token_model)
    @api.response(200, 'Login successful')
    @api.response(401, 'Invalid credentials')
    @limiter.limit("5 per minute")
    def post(self):
        """Login and get tokens."""
        data = request.json

        try:
            user = AuthService.authenticate_user(
                email=data['email'],
                password=data['password']
            )

            tokens = AuthService.create_tokens(user.id)
            return tokens, 200

        except ValueError as e:
            api.abort(401, str(e))
        except Exception as e:
            api.abort(500, 'Login failed')


@api.route('/refresh')
class Refresh(Resource):
    """Token refresh."""

    @jwt_required(refresh=True)
    @api.marshal_with(token_model)
    @api.response(200, 'Token refreshed')
    @limiter.limit("10 per minute")
    def post(self):
        """Refresh access token."""
        user_id = get_jwt_identity()
        tokens = AuthService.create_tokens(user_id)
        return {'access_token': tokens['access_token']}, 200


@api.route('/me')
class Me(Resource):
    """Current user info."""

    @jwt_required()
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def get(self):
        """Get current user information."""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            api.abort(404, 'User not found')

        return {
            'success': True,
            'data': user.to_dict()
        }, 200
```

**Step 2: Update app/api/__init__.py**

```python
"""API package."""
from app.api.health import api as health_ns
from app.schemas.auth import api as auth_ns

__all__ = ['health_ns', 'auth_ns']
```

**Step 3: Update app/__init__.py to register auth namespace**

```python
# Update the register namespaces section:
from app.api import health_ns
from app.schemas.auth import api as auth_ns
api.add_namespace(health_ns, path='/api/health')
api.add_namespace(auth_ns, path='/api/auth')
```

**Step 4: Commit**

```bash
git add app/api/auth.py app/api/__init__.py app/__init__.py
git commit -m "feat: add authentication API endpoints"
```

---

## Task 10: User Service and API

**Files:**
- Create: `app/services/user_service.py`
- Create: `app/api/users.py`
- Modify: `app/services/__init__.py`
- Modify: `app/api/__init__.py`
- Modify: `app/__init__.py`

**Step 1: Create app/services/user_service.py**

```python
"""User service."""
from app.models.user import User
from app.extensions import db


class UserService:
    """User service."""

    @staticmethod
    def get_users(page=1, per_page=10):
        """Get paginated list of users."""
        pagination = User.query.filter_by(is_active=True).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError('User not found')
        return user

    @staticmethod
    def update_user(user_id, data):
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ValueError('Email already in use')
            user.email = data['email']

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """Soft delete user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        user.is_active = False
        db.session.commit()
        return user
```

**Step 2: Create app/api/users.py**

```python
"""Users API."""
from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required
from app.schemas.user import api, user_model, user_input_model, user_list_model
from app.services.user_service import UserService


@api.route('')
class UserList(Resource):
    """User list resource."""

    @jwt_required()
    @api.marshal_with(user_list_model)
    @api.response(200, 'Success')
    @api.doc(params={
        'page': 'Page number (default: 1)',
        'per_page': 'Items per page (default: 10)'
    })
    def get(self):
        """Get list of users."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        result = UserService.get_users(page=page, per_page=per_page)
        return result, 200


@api.route('/<int:user_id>')
class UserDetail(Resource):
    """User detail resource."""

    @jwt_required()
    @api.marshal_with(user_model)
    @api.response(200, 'Success')
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get user by ID."""
        try:
            user = UserService.get_user_by_id(user_id)
            return user.to_dict(), 200
        except ValueError as e:
            api.abort(404, str(e))

    @jwt_required()
    @api.expect(user_input_model, validate=True)
    @api.marshal_with(user_model)
    @api.response(200, 'User updated')
    @api.response(400, 'Validation error')
    @api.response(404, 'User not found')
    def put(self, user_id):
        """Update user."""
        try:
            user = UserService.update_user(user_id, request.json)
            return user.to_dict(), 200
        except ValueError as e:
            api.abort(400, str(e))

    @jwt_required()
    @api.response(204, 'User deleted')
    @api.response(404, 'User not found')
    def delete(self, user_id):
        """Delete user (soft delete)."""
        try:
            UserService.delete_user(user_id)
            return '', 204
        except ValueError as e:
            api.abort(404, str(e))
```

**Step 3: Update app/services/__init__.py**

```python
"""Services package."""
from app.services.auth_service import AuthService
from app.services.user_service import UserService

__all__ = ['AuthService', 'UserService']
```

**Step 4: Update app/api/__init__.py**

```python
"""API package."""
from app.api.health import api as health_ns
from app.schemas.auth import api as auth_ns
from app.schemas.user import api as users_ns

__all__ = ['health_ns', 'auth_ns', 'users_ns']
```

**Step 5: Update app/__init__.py**

```python
# Update register namespaces section:
from app.api import health_ns
from app.schemas.auth import api as auth_ns
from app.schemas.user import api as users_ns
api.add_namespace(health_ns, path='/api/health')
api.add_namespace(auth_ns, path='/api/auth')
api.add_namespace(users_ns, path='/api/users')
```

**Step 6: Commit**

```bash
git add app/services/user_service.py app/api/users.py app/services/__init__.py app/api/__init__.py app/__init__.py
git commit -m "feat: add user service and API endpoints"
```

---

## Task 11: Celery Configuration

**Files:**
- Create: `celery_worker.py`
- Create: `app/tasks/__init__.py`
- Create: `app/tasks/email_tasks.py`

**Step 1: Create celery_worker.py**

```python
"""Celery worker entry point."""
import os
from app import create_app
from app.extensions import celery

# Create Flask app and push context
app = create_app(os.getenv('FLASK_ENV', 'development'))
app.app_context().push()
```

**Step 2: Create app/tasks/email_tasks.py**

```python
"""Email tasks."""
from app.extensions import celery
from app.models.user import User


@celery.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """Send welcome email to new user."""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f'User {user_id} not found')

        # TODO: Implement actual email sending
        # For now, just log
        print(f'Sending welcome email to {user.email}')

        return f'Welcome email sent to {user.email}'

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, token):
    """Send password reset email."""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f'User {user_id} not found')

        # TODO: Implement actual email sending
        print(f'Sending password reset email to {user.email}')

        return f'Password reset email sent to {user.email}'

    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task
def send_notification(user_id, message):
    """Send notification email."""
    user = User.query.get(user_id)
    if not user:
        return f'User {user_id} not found'

    # TODO: Implement actual email sending
    print(f'Sending notification to {user.email}: {message}')

    return f'Notification sent to {user.email}'
```

**Step 3: Create app/tasks/__init__.py**

```python
"""Tasks package."""
from app.tasks.email_tasks import (
    send_welcome_email,
    send_password_reset_email,
    send_notification
)

__all__ = [
    'send_welcome_email',
    'send_password_reset_email',
    'send_notification'
]
```

**Step 4: Commit**

```bash
git add celery_worker.py app/tasks/
git commit -m "feat: add Celery configuration and email tasks"
```

---

## Task 12: Docker Configuration

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker/gunicorn.conf.py`
- Create: `docker/nginx.conf`
- Create: `docker-compose.yml`

**Step 1: Create docker/Dockerfile**

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')"

EXPOSE 5000

CMD ["gunicorn", "--config", "docker/gunicorn.conf.py", "wsgi:app"]
```

**Step 2: Create docker/gunicorn.conf.py**

```python
"""Gunicorn configuration."""
import multiprocessing

# Server socket
bind = '0.0.0.0:5000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
threads = 2
timeout = 60
keepalive = 2

# Logging
accesslog = '/app/logs/access.log'
errorlog = '/app/logs/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'flask_app'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

**Step 3: Create docker/nginx.conf**

```nginx
upstream flask_app {
    server app:5000;
}

server {
    listen 80;
    server_name localhost;
    client_max_body_size 10M;

    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if needed)
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /api/health {
        proxy_pass http://flask_app/api/health;
        access_log off;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/json application/javascript;
}
```

**Step 4: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: flask_app
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mysql+pymysql://flask_user:flask_password@mysql:3306/flask_app
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - backend

  nginx:
    image: nginx:1.25-alpine
    container_name: flask_nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app
    networks:
      - backend

  mysql:
    image: mysql:8.0
    container_name: flask_mysql
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: flask_app
      MYSQL_USER: flask_user
      MYSQL_PASSWORD: flask_password
      MYSQL_ROOT_PASSWORD: root_password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - backend

  redis:
    image: redis:7-alpine
    container_name: flask_redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - backend

  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: flask_celery_worker
    restart: unless-stopped
    command: celery -A celery_worker.celery worker --loglevel=info
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mysql+pymysql://flask_user:flask_password@mysql:3306/flask_app
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - backend

volumes:
  mysql_data:
  redis_data:

networks:
  backend:
    driver: bridge
```

**Step 5: Commit**

```bash
git add docker/
git add docker-compose.yml
git commit -m "feat: add Docker configuration"
```

---

## Task 13: Testing Setup

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`
- Create: `tests/test_users.py`

**Step 1: Create tests/conftest.py**

```python
"""Pytest configuration and fixtures."""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        # Clean up before test
        User.query.delete()
        db.session.commit()

        yield db

        # Clean up after test
        db.session.rollback()


@pytest.fixture(scope='function')
def sample_user(db_session):
    """Create sample user."""
    user = User(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    user.set_password('password123')
    user.save()
    return user


@pytest.fixture(scope='function')
def auth_headers(client, sample_user):
    """Get authentication headers."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    data = response.get_json()
    access_token = data['access_token']

    return {
        'Authorization': f'Bearer {access_token}'
    }
```

**Step 2: Create tests/test_auth.py**

```python
"""Authentication API tests."""
import pytest


def test_register_success(client, db_session):
    """Test successful user registration."""
    response = client.post('/api/auth/register', json={
        'email': 'newuser@example.com',
        'password': 'password123',
        'first_name': 'New',
        'last_name': 'User'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['email'] == 'newuser@example.com'


def test_register_duplicate_email(client, sample_user):
    """Test registration with duplicate email."""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    assert response.status_code == 400


def test_login_success(client, sample_user):
    """Test successful login."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data


def test_login_invalid_credentials(client, sample_user):
    """Test login with invalid credentials."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })

    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get('/api/auth/me', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['email'] == 'test@example.com'


def test_unauthorized_access(client):
    """Test accessing protected endpoint without auth."""
    response = client.get('/api/auth/me')

    assert response.status_code == 401
```

**Step 3: Create tests/test_users.py**

```python
"""User API tests."""
import pytest


def test_get_users_list(client, auth_headers, sample_user):
    """Test getting users list."""
    response = client.get('/api/users', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    assert data['total'] >= 1


def test_get_user_detail(client, auth_headers, sample_user):
    """Test getting user detail."""
    response = client.get(f'/api/users/{sample_user.id}', headers=auth_headers)

    assert response.status_code == 200
    assert 'email' in response.get_json()


def test_update_user(client, auth_headers, sample_user):
    """Test updating user."""
    response = client.put(
        f'/api/users/{sample_user.id}',
        headers=auth_headers,
        json={'first_name': 'Updated'}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['first_name'] == 'Updated'


def test_delete_user(client, auth_headers, sample_user):
    """Test deleting user."""
    response = client.delete(
        f'/api/users/{sample_user.id}',
        headers=auth_headers
    )

    assert response.status_code == 204


def test_get_nonexistent_user(client, auth_headers):
    """Test getting nonexistent user."""
    response = client.get('/api/users/99999', headers=auth_headers)

    assert response.status_code == 404
```

**Step 4: Run tests**

```bash
pytest -v tests/
```

Expected: Tests should pass (may have some failures, we'll fix in next steps)

**Step 5: Commit**

```bash
git add tests/
git commit -m "test: add pytest configuration and tests"
```

---

## Task 14: README Documentation

**Files:**
- Create: `README.md`

**Step 1: Create README.md**

```markdown
# Flask Production REST API Template

Production-ready Flask REST API backend template with JWT authentication, Celery async tasks, and Docker deployment.

## Features

- **Flask 3.x** with Application Factory pattern
- **Flask-RESTX** for automatic Swagger/OpenAPI documentation
- **JWT Authentication** with access and refresh tokens
- **SQLAlchemy ORM** with MySQL support
- **Celery** for asynchronous task processing
- **Redis** for caching and task queue
- **Rate Limiting** with Flask-Limiter
- **CORS** configuration
- **Structured JSON logging**
- **Docker & Docker Compose** for easy deployment
- **pytest** test suite with fixtures
- **Blueprint-based** modular architecture

## Tech Stack

- **Web Framework**: Flask 3.0.3, Flask-RESTX 1.3.0
- **Database**: MySQL 8.0 with SQLAlchemy ORM
- **Authentication**: Flask-JWT-Extended with bcrypt
- **Task Queue**: Celery 5.3 with Redis broker
- **Cache/Queue**: Redis 7
- **WSGI Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Testing**: pytest, pytest-flask

## Project Structure

```
flask_template/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   ├── models/              # Database models
│   ├── api/                 # API endpoints
│   ├── schemas/             # Request/response schemas
│   ├── services/            # Business logic
│   ├── tasks/               # Celery tasks
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── logs/                    # Application logs
├── migrations/              # Database migrations
├── docker-compose.yml       # Docker services
├── requirements.txt         # Python dependencies
└── wsgi.py                  # WSGI entry point
```

## Quick Start

### Local Development

1. **Clone and setup**

```bash
git clone <repository-url>
cd flask_template
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start services with Docker**

```bash
docker-compose up -d mysql redis
```

4. **Initialize database**

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Run development server**

```bash
flask run
```

6. **Run Celery worker** (in separate terminal)

```bash
celery -A celery_worker.celery worker --loglevel=info
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build -d

# Run migrations
docker-compose exec app flask db upgrade

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:5000/api/docs
- **Health Check**: http://localhost:5000/api/health

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Users

- `GET /api/users` - List users (paginated)
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user (soft delete)

### Health

- `GET /api/health` - Service health check

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/flask_app

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/2
```

## Development

### Code Formatting

```bash
black app/ tests/
flake8 app/ tests/
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Create service in `app/services/`
3. Create API endpoint in `app/api/`
4. Register namespace in `app/__init__.py`
5. Add tests in `tests/`

## Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Generate strong `SECRET_KEY` and `JWT_SECRET_KEY`
3. Configure production database URL
4. Set proper `CORS_ORIGINS`
5. Use `docker-compose up -d` for deployment
6. Set up SSL/TLS with Let's Encrypt
7. Configure log aggregation (ELK, Datadog, etc.)
8. Set up monitoring (Prometheus, Grafana, etc.)

## Security

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- Rate limiting on authentication endpoints
- CORS configuration
- SQL injection protection via SQLAlchemy ORM
- Input validation with Flask-RESTX

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 15: Final Verification

**Files:**
- None (verification only)

**Step 1: Check all files are in place**

```bash
# Check structure
ls -R app/ tests/ docker/

# Verify key files exist
ls requirements.txt docker-compose.yml wsgi.py celery_worker.py
```

**Step 2: Install dependencies and run tests**

```bash
pip install -r requirements-dev.txt
pytest -v tests/
```

Expected: All tests pass

**Step 3: Test Docker build**

```bash
docker-compose build
```

Expected: Build succeeds without errors

**Step 4: Start full stack**

```bash
docker-compose up -d
docker-compose ps
```

Expected: All services running

**Step 5: Test health endpoint**

```bash
curl http://localhost/api/health
```

Expected: JSON response with status "healthy"

**Step 6: Test Swagger UI**

Open browser: http://localhost/api/docs

Expected: Swagger UI loads with all endpoints documented

**Step 7: Cleanup**

```bash
docker-compose down -v
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] All dependencies install without errors
- [ ] Tests pass with pytest
- [ ] Docker containers build successfully
- [ ] All services start and run healthy
- [ ] Health check endpoint responds
- [ ] Swagger UI displays API documentation
- [ ] Can register a new user via API
- [ ] Can login and receive JWT tokens
- [ ] Protected endpoints require authentication
- [ ] Rate limiting works on auth endpoints
- [ ] Database migrations run successfully
- [ ] Celery worker connects and processes tasks
- [ ] Logs are written to logs/ directory in JSON format
- [ ] README is comprehensive and accurate

## Next Steps (Optional Enhancements)

### Planned Enhancements

1. **OAuth2 Social Login**: Add Google/GitHub OAuth
2. **WebSocket**: Real-time features with Flask-SocketIO
3. **Caching**: Redis caching decorator for expensive operations
4. **Metrics**: Prometheus metrics export
5. **Error Tracking**: Sentry integration
6. **CI/CD**: GitHub Actions workflow
7. **API Versioning**: Support /api/v1, /api/v2
8. **Pagination**: Link headers and HATEOAS
9. **Background Jobs UI**: Flower dashboard for Celery

### On Hold (Pending Infrastructure)

1. **File Upload**: AWS S3 integration (Pending deployment server decision)

---

## Plan Complete

**Plan saved to:** `docs/plans/2026-01-09-flask-production-template.md`

**Execution Options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach do you prefer?
