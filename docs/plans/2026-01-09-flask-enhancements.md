# Flask Template 향후 확장 기능 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add optional enhancements to Flask production template (OAuth2, WebSocket, Caching, Metrics, CI/CD, etc.)

**Prerequisites:** Complete Tasks 1-15 from `2026-01-09-flask-production-template.md` first

**Tech Stack:** Authlib, Flask-SocketIO, Prometheus, Sentry, GitHub Actions

---

## Task 16: OAuth2 Social Login (Google)

**Files:**
- Modify: `requirements.txt`
- Create: `app/services/oauth_service.py`
- Create: `app/api/oauth.py`
- Modify: `app/__init__.py`
- Modify: `app/config.py`
- Modify: `.env.example`

**Step 1: Add OAuth dependencies to requirements.txt**

```txt
authlib==1.3.0
httpx==0.27.0
```

**Step 2: Update app/config.py with OAuth settings**

Add to BaseConfig class:

```python
# OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/oauth/google/callback')
```

**Step 3: Create app/services/oauth_service.py**

```python
"""OAuth service."""
from authlib.integrations.requests_client import OAuth2Session
from flask import current_app
from app.models.user import User
from app.services.auth_service import AuthService


class OAuthService:
    """OAuth service for social login."""

    @staticmethod
    def get_google_oauth_session():
        """Get Google OAuth2 session."""
        return OAuth2Session(
            client_id=current_app.config['GOOGLE_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_CLIENT_SECRET'],
            redirect_uri=current_app.config['GOOGLE_REDIRECT_URI'],
            scope='openid email profile'
        )

    @staticmethod
    def get_google_auth_url():
        """Get Google authorization URL."""
        session = OAuthService.get_google_oauth_session()
        authorization_url, state = session.create_authorization_url(
            'https://accounts.google.com/o/oauth2/v2/auth'
        )
        return authorization_url, state

    @staticmethod
    def handle_google_callback(code):
        """Handle Google OAuth callback."""
        session = OAuthService.get_google_oauth_session()

        # Exchange code for token
        token = session.fetch_token(
            'https://oauth2.googleapis.com/token',
            code=code
        )

        # Get user info
        resp = session.get('https://www.googleapis.com/oauth2/v1/userinfo')
        user_info = resp.json()

        # Find or create user
        user = User.query.filter_by(email=user_info['email']).first()

        if not user:
            # Create new user from OAuth
            user = User(
                email=user_info['email'],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                password_hash='oauth_user'  # No password for OAuth users
            )
            user.save()

        # Create JWT tokens
        return AuthService.create_tokens(user.id)
```

**Step 4: Create app/api/oauth.py**

```python
"""OAuth API endpoints."""
from flask import request, redirect
from flask_restx import Namespace, Resource
from app.services.oauth_service import OAuthService

api = Namespace('oauth', description='OAuth operations')


@api.route('/google/login')
class GoogleLogin(Resource):
    """Google OAuth login."""

    @api.response(302, 'Redirect to Google')
    def get(self):
        """Redirect to Google OAuth."""
        auth_url, state = OAuthService.get_google_auth_url()
        return redirect(auth_url)


@api.route('/google/callback')
class GoogleCallback(Resource):
    """Google OAuth callback."""

    @api.response(200, 'Login successful')
    @api.response(400, 'Invalid authorization code')
    def get(self):
        """Handle Google OAuth callback."""
        code = request.args.get('code')

        if not code:
            api.abort(400, 'Authorization code not provided')

        try:
            tokens = OAuthService.handle_google_callback(code)
            return {
                'success': True,
                'data': tokens
            }, 200
        except Exception as e:
            api.abort(500, f'OAuth failed: {str(e)}')
```

**Step 5: Update app/services/__init__.py**

```python
from app.services.oauth_service import OAuthService

__all__ = ['AuthService', 'UserService', 'OAuthService']
```

**Step 6: Update app/api/__init__.py**

```python
from app.api.oauth import api as oauth_ns

__all__ = ['health_ns', 'auth_ns', 'users_ns', 'oauth_ns']
```

**Step 7: Register OAuth namespace in app/__init__.py**

```python
from app.api import oauth_ns
api.add_namespace(oauth_ns, path='/api/oauth')
```

**Step 8: Update .env.example**

```bash
# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/oauth/google/callback
```

**Step 9: Test OAuth flow**

```bash
# Start app
flask run

# Navigate to
open http://localhost:5000/api/oauth/google/login
```

Expected: Redirects to Google login, then back with tokens

**Step 10: Commit**

```bash
git add .
git commit -m "feat: add Google OAuth2 social login"
```

---

## Task 17: WebSocket Real-time Features

**Files:**
- Modify: `requirements.txt`
- Create: `app/websocket.py`
- Modify: `app/__init__.py`
- Create: `app/events/__init__.py`
- Create: `app/events/notifications.py`
- Modify: `wsgi.py`

**Step 1: Add WebSocket dependencies**

```txt
flask-socketio==5.3.6
python-socketio==5.11.1
```

**Step 2: Create app/websocket.py**

```python
"""WebSocket configuration."""
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")
```

**Step 3: Create app/events/notifications.py**

```python
"""WebSocket event handlers."""
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from app.websocket import socketio


@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection."""
    try:
        # Verify JWT token
        token = auth.get('token')
        if token:
            decoded = decode_token(token)
            user_id = decoded['sub']

            # Join user's personal room
            join_room(f'user_{user_id}')
            emit('connected', {'message': 'Connected successfully'})
            return True
        else:
            return False
    except Exception as e:
        print(f'Connection error: {e}')
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


@socketio.on('subscribe_notifications')
def handle_subscribe(data):
    """Subscribe to notification channel."""
    channel = data.get('channel')
    if channel:
        join_room(channel)
        emit('subscribed', {'channel': channel})


@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message."""
    message = data.get('message')
    room = data.get('room', 'general')

    emit('new_message', {
        'message': message,
        'room': room
    }, room=room)


def send_notification_to_user(user_id, message):
    """Send notification to specific user."""
    socketio.emit(
        'notification',
        {'message': message},
        room=f'user_{user_id}'
    )
```

**Step 4: Create app/events/__init__.py**

```python
"""Events package."""
from app.events.notifications import send_notification_to_user

__all__ = ['send_notification_to_user']
```

**Step 5: Initialize SocketIO in app/__init__.py**

```python
from app.websocket import socketio

def create_app(config_name='default'):
    # ... existing code ...

    # Initialize SocketIO
    socketio.init_app(
        app,
        message_queue=app.config['REDIS_URL'],
        async_mode='threading'
    )

    # Import event handlers
    from app.events import notifications

    return app
```

**Step 6: Update wsgi.py for SocketIO**

```python
"""WSGI entry point for production."""
import os
from app import create_app
from app.websocket import socketio

app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
```

**Step 7: Create JavaScript client example**

Create `examples/websocket_client.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>WebSocket Test</h1>
    <div id="status">Disconnected</div>
    <div id="messages"></div>

    <script>
        const token = 'YOUR_JWT_TOKEN_HERE';

        const socket = io('http://localhost:5000', {
            auth: { token: token }
        });

        socket.on('connect', () => {
            document.getElementById('status').textContent = 'Connected';
        });

        socket.on('connected', (data) => {
            console.log('Connected:', data);
        });

        socket.on('notification', (data) => {
            const div = document.createElement('div');
            div.textContent = 'Notification: ' + data.message;
            document.getElementById('messages').appendChild(div);
        });

        socket.on('disconnect', () => {
            document.getElementById('status').textContent = 'Disconnected';
        });
    </script>
</body>
</html>
```

**Step 8: Test WebSocket**

```bash
# Start app
flask run

# Open examples/websocket_client.html in browser
```

**Step 9: Commit**

```bash
git add .
git commit -m "feat: add WebSocket real-time features with Flask-SocketIO"
```

---

## Task 18: Redis Caching Decorator

**Files:**
- Create: `app/utils/cache.py`
- Modify: `app/utils/__init__.py`
- Modify: `app/services/user_service.py`
- Create: `tests/test_cache.py`

**Step 1: Create app/utils/cache.py**

```python
"""Caching utilities."""
import json
import hashlib
from functools import wraps
from flask import current_app
import redis


def get_redis_client():
    """Get Redis client."""
    return redis.from_url(current_app.config['REDIS_URL'])


def cache_key(*args, **kwargs):
    """Generate cache key from function arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl=300, key_prefix=''):
    """
    Cache decorator for expensive operations.

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl=600, key_prefix='user_list')
        def get_users():
            return expensive_query()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            r = get_redis_client()
            cached_result = r.get(cache_key_str)

            if cached_result:
                current_app.logger.info(f'Cache hit: {cache_key_str}')
                return json.loads(cached_result)

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            r.setex(cache_key_str, ttl, json.dumps(result, default=str))
            current_app.logger.info(f'Cache miss: {cache_key_str}')

            return result

        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    """
    Invalidate cache by pattern.

    Args:
        key_pattern: Redis key pattern (e.g., 'user_list:*')
    """
    r = get_redis_client()
    keys = r.keys(key_pattern)
    if keys:
        r.delete(*keys)
        return len(keys)
    return 0


def clear_all_cache():
    """Clear all cache entries."""
    r = get_redis_client()
    return r.flushdb()
```

**Step 2: Update app/utils/__init__.py**

```python
from app.utils.logger import setup_logging
from app.utils.cache import cached, invalidate_cache, clear_all_cache

__all__ = ['setup_logging', 'cached', 'invalidate_cache', 'clear_all_cache']
```

**Step 3: Update app/services/user_service.py to use caching**

```python
from app.utils.cache import cached, invalidate_cache

class UserService:
    @staticmethod
    @cached(ttl=600, key_prefix='user_list')
    def get_users(page=1, per_page=10):
        """Get paginated list of users (cached for 10 minutes)."""
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
    def update_user(user_id, data):
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        # Update fields...
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ValueError('Email already in use')
            user.email = data['email']

        db.session.commit()

        # Invalidate cache after update
        invalidate_cache('user_list:*')

        return user

    @staticmethod
    def delete_user(user_id):
        """Soft delete user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')

        user.is_active = False
        db.session.commit()

        # Invalidate cache after delete
        invalidate_cache('user_list:*')

        return user
```

**Step 4: Create tests/test_cache.py**

```python
"""Cache tests."""
import time
import pytest
from app.utils.cache import cached, invalidate_cache


@cached(ttl=2, key_prefix='test')
def expensive_operation(x):
    """Simulate expensive operation."""
    time.sleep(0.1)
    return x * 2


def test_cache_hit(app):
    """Test cache hit."""
    with app.app_context():
        # First call - cache miss
        start = time.time()
        result1 = expensive_operation(5)
        duration1 = time.time() - start
        assert result1 == 10

        # Second call - cache hit (should be much faster)
        start = time.time()
        result2 = expensive_operation(5)
        duration2 = time.time() - start
        assert result2 == 10
        assert duration2 < duration1


def test_cache_expiration(app):
    """Test cache expiration."""
    with app.app_context():
        result1 = expensive_operation(5)
        assert result1 == 10

        # Wait for cache to expire
        time.sleep(3)

        result2 = expensive_operation(5)
        assert result2 == 10


def test_cache_invalidation(app):
    """Test cache invalidation."""
    with app.app_context():
        expensive_operation(5)

        # Invalidate cache
        count = invalidate_cache('test:*')
        assert count >= 0

        # Should recalculate
        result = expensive_operation(5)
        assert result == 10
```

**Step 5: Run tests**

```bash
pytest tests/test_cache.py -v
```

Expected: All cache tests pass

**Step 6: Commit**

```bash
git add app/utils/cache.py tests/test_cache.py
git commit -m "feat: add Redis caching decorator for expensive operations"
```

---

## Task 19: Prometheus Metrics

**Files:**
- Modify: `requirements.txt`
- Create: `app/utils/metrics.py`
- Create: `app/api/metrics.py`
- Modify: `app/__init__.py`
- Modify: `app/services/auth_service.py`

**Step 1: Add Prometheus dependencies**

```txt
prometheus-client==0.20.0
prometheus-flask-exporter==0.23.0
```

**Step 2: Create app/utils/metrics.py**

```python
"""Prometheus metrics."""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_flask_exporter import PrometheusMetrics

# Custom business metrics
user_registrations = Counter(
    'user_registrations_total',
    'Total number of user registrations'
)

user_logins = Counter(
    'user_logins_total',
    'Total number of successful user logins'
)

failed_logins = Counter(
    'failed_logins_total',
    'Total number of failed login attempts'
)

active_users = Gauge(
    'active_users_count',
    'Number of currently active users'
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint', 'status']
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name', 'status']
)

cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)


def init_metrics(app):
    """Initialize Prometheus metrics."""
    # Flask-RESTX conflicts with PrometheusMetrics auto-discovery
    # So we disable default metrics and add custom ones
    metrics = PrometheusMetrics(
        app,
        path=None,  # Disable default /metrics endpoint
        export_defaults=True,
        defaults_prefix='flask'
    )

    # Add application info
    app_info = Info('flask_app', 'Flask application information')
    app_info.info({
        'version': '1.0.0',
        'environment': app.config.get('ENV', 'production')
    })

    return metrics
```

**Step 3: Create app/api/metrics.py**

```python
"""Metrics API endpoint."""
from flask import Response
from flask_restx import Namespace, Resource
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

api = Namespace('metrics', description='Prometheus metrics')


@api.route('')
class Metrics(Resource):
    """Prometheus metrics endpoint."""

    @api.doc(security=None)  # Public endpoint
    def get(self):
        """
        Export Prometheus metrics.

        Returns metrics in Prometheus text format.
        """
        return Response(
            generate_latest(),
            mimetype=CONTENT_TYPE_LATEST
        )
```

**Step 4: Update app/__init__.py**

```python
from app.utils.metrics import init_metrics
from app.api.metrics import api as metrics_ns

def create_app(config_name='default'):
    # ... existing code ...

    # Initialize metrics (skip for testing)
    if config_name != 'testing':
        init_metrics(app)

    # Register metrics namespace
    api.add_namespace(metrics_ns, path='/metrics')

    return app
```

**Step 5: Add metrics to auth service**

Update `app/services/auth_service.py`:

```python
from app.utils.metrics import user_registrations, user_logins, failed_logins, active_users

class AuthService:
    @staticmethod
    def register_user(email, password, first_name, last_name):
        """Register a new user."""
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()

        # Increment metrics
        user_registrations.inc()
        active_users.set(User.query.filter_by(is_active=True).count())

        return user

    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user and return user object."""
        user = User.query.filter_by(email=email, is_active=True).first()

        if not user or not user.check_password(password):
            failed_logins.inc()
            raise ValueError('Invalid email or password')

        user.last_login = datetime.utcnow()
        db.session.commit()

        # Increment metrics
        user_logins.inc()

        return user
```

**Step 6: Add cache metrics**

Update `app/utils/cache.py`:

```python
from app.utils.metrics import cache_hits, cache_misses

def cached(ttl=300, key_prefix=''):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            r = get_redis_client()
            cached_result = r.get(cache_key_str)

            if cached_result:
                current_app.logger.info(f'Cache hit: {cache_key_str}')
                cache_hits.labels(cache_type=key_prefix or 'default').inc()
                return json.loads(cached_result)

            result = func(*args, **kwargs)
            r.setex(cache_key_str, ttl, json.dumps(result, default=str))
            current_app.logger.info(f'Cache miss: {cache_key_str}')
            cache_misses.labels(cache_type=key_prefix or 'default').inc()

            return result
        return wrapper
    return decorator
```

**Step 7: Test metrics endpoint**

```bash
# Start app
flask run

# Check metrics
curl http://localhost:5000/metrics
```

Expected: Prometheus format metrics output

**Step 8: Create Prometheus config example**

Create `examples/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'flask-app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

**Step 9: Commit**

```bash
git add .
git commit -m "feat: add Prometheus metrics export"
```

---

## Task 20: Sentry Error Tracking

**Files:**
- Modify: `requirements.txt`
- Modify: `app/__init__.py`
- Modify: `app/config.py`
- Create: `app/utils/sentry.py`
- Modify: `.env.example`

**Step 1: Add Sentry dependency**

```txt
sentry-sdk[flask]==1.40.0
```

**Step 2: Update app/config.py**

Add to BaseConfig:

```python
# Sentry
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0'))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '1.0'))
```

**Step 3: Initialize Sentry in app/__init__.py**

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize Sentry
    if app.config.get('SENTRY_DSN') and config_name != 'testing':
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[
                FlaskIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration()
            ],
            environment=app.config['SENTRY_ENVIRONMENT'],
            traces_sample_rate=app.config['SENTRY_TRACES_SAMPLE_RATE'],
            profiles_sample_rate=app.config['SENTRY_PROFILES_SAMPLE_RATE'],
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            max_breadcrumbs=50
        )
        app.logger.info('Sentry initialized')

    # ... rest of initialization ...
```

**Step 4: Create app/utils/sentry.py**

```python
"""Sentry utilities."""
import sentry_sdk
from flask import request, g
from flask_jwt_extended import get_jwt_identity


def capture_exception_with_context(exception, extra_context=None):
    """
    Capture exception with additional context.

    Args:
        exception: The exception to capture
        extra_context: Additional context dictionary
    """
    with sentry_sdk.push_scope() as scope:
        # Add user context
        try:
            user_id = get_jwt_identity()
            if user_id:
                scope.set_user({"id": user_id})
        except:
            pass

        # Add request context
        try:
            scope.set_context("request", {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "data": request.get_json(silent=True),
            })
        except:
            pass

        # Add extra context
        if extra_context:
            scope.set_context("extra", extra_context)

        # Add tags
        scope.set_tag("environment", "production")

        sentry_sdk.capture_exception(exception)


def capture_message(message, level='info', extra_context=None):
    """
    Capture a message.

    Args:
        message: The message to capture
        level: Message level (info, warning, error)
        extra_context: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        if extra_context:
            scope.set_context("extra", extra_context)

        sentry_sdk.capture_message(message, level=level)


def add_breadcrumb(message, category='default', level='info', data=None):
    """
    Add a breadcrumb.

    Args:
        message: Breadcrumb message
        category: Category of the breadcrumb
        level: Severity level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )
```

**Step 5: Use Sentry in error handlers**

Update `app/__init__.py` error handlers:

```python
from app.utils.sentry import capture_exception_with_context

def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(500)
    def internal_error(error):
        # Capture exception in Sentry
        capture_exception_with_context(error, {
            'error_type': 'internal_server_error'
        })

        app.logger.error(f'Internal error: {error}')
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }), 500
```

**Step 6: Add Sentry to Celery tasks**

Update `app/tasks/email_tasks.py`:

```python
from app.utils.sentry import capture_exception_with_context, add_breadcrumb

@celery.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """Send welcome email to new user."""
    add_breadcrumb(f'Starting send_welcome_email for user {user_id}', category='celery')

    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f'User {user_id} not found')

        # TODO: Implement actual email sending
        print(f'Sending welcome email to {user.email}')

        return f'Welcome email sent to {user.email}'

    except Exception as e:
        capture_exception_with_context(e, {
            'task_name': 'send_welcome_email',
            'user_id': user_id
        })
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

**Step 7: Update .env.example**

```bash
# Sentry
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

**Step 8: Create test endpoint**

Add to any API file for testing:

```python
@api.route('/test-sentry')
class TestSentry(Resource):
    """Test Sentry integration."""

    def get(self):
        """Trigger a test error."""
        try:
            result = 1 / 0
        except Exception as e:
            from app.utils.sentry import capture_exception_with_context
            capture_exception_with_context(e, {'test': True})
            raise

        return {'message': 'This should not be reached'}
```

**Step 9: Test Sentry**

```bash
# Set SENTRY_DSN in .env
# Start app
flask run

# Trigger test error
curl http://localhost:5000/api/test-sentry
```

Check Sentry dashboard for the captured error.

**Step 10: Commit**

```bash
git add .
git commit -m "feat: add Sentry error tracking integration"
```

---

## Task 21: GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`
- Create: `.github/dependabot.yml`

**Step 1: Create .github/workflows/ci.yml**

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install black flake8

    - name: Check formatting with black
      run: black --check app/ tests/

    - name: Lint with flake8
      run: flake8 app/ tests/ --max-line-length=120 --exclude=migrations

  test:
    name: Test
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping --silent"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      env:
        DATABASE_URL: mysql+pymysql://root:test_password@localhost:3306/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key-for-ci
        JWT_SECRET_KEY: test-jwt-secret-key-for-ci
        FLASK_ENV: testing
      run: |
        pytest -v --cov=app --cov-report=xml --cov-report=term --cov-fail-under=70

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
        verbose: true

  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

  build:
    name: Build Docker
    needs: [lint, test]
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build Docker image
      run: docker-compose build app

    - name: Test Docker image
      run: |
        docker-compose up -d
        sleep 10
        docker-compose ps
        docker-compose logs app
        docker-compose down
```

**Step 2: Create .github/workflows/deploy.yml**

```yaml
name: Deploy

on:
  push:
    branches: [ main ]
  release:
    types: [ published ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./docker/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    name: Deploy to Server
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Deploy to production server
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.DEPLOY_HOST }}
        username: ${{ secrets.DEPLOY_USER }}
        key: ${{ secrets.DEPLOY_SSH_KEY }}
        port: ${{ secrets.DEPLOY_PORT || 22 }}
        script: |
          cd /opt/flask-app
          docker-compose pull
          docker-compose up -d --force-recreate
          docker-compose exec -T app flask db upgrade
          docker system prune -af

    - name: Notify deployment
      if: always()
      run: |
        echo "Deployment completed: ${{ job.status }}"
        # Add Slack/Discord notification here if needed
```

**Step 3: Create .github/dependabot.yml**

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 5
    reviewers:
      - "your-github-username"
    labels:
      - "dependencies"
      - "python"

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/docker"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 3
    labels:
      - "dependencies"
      - "docker"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 3
    labels:
      - "dependencies"
      - "github-actions"
```

**Step 4: Create GitHub secrets documentation**

Create `docs/github-secrets.md`:

```markdown
# GitHub Secrets Configuration

Required secrets for CI/CD:

## Deployment Secrets

- `DEPLOY_HOST`: Production server hostname/IP
- `DEPLOY_USER`: SSH username for deployment
- `DEPLOY_SSH_KEY`: SSH private key for deployment
- `DEPLOY_PORT`: SSH port (optional, default 22)

## Optional Secrets

- `DOCKER_USERNAME`: Docker Hub username (if using Docker Hub)
- `DOCKER_PASSWORD`: Docker Hub password
- `SLACK_WEBHOOK`: Slack webhook for notifications
- `CODECOV_TOKEN`: Codecov token for coverage reports

## Setting Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its value
```

**Step 5: Create .github/workflows/manual-deploy.yml** (optional)

```yaml
name: Manual Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        type: choice
        options:
          - staging
          - production
      version:
        description: 'Docker image tag to deploy'
        required: true
        default: 'latest'

jobs:
  deploy:
    name: Deploy to ${{ github.event.inputs.environment }}
    runs-on: ubuntu-latest

    steps:
    - name: Deploy
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets[format('DEPLOY_HOST_{0}', github.event.inputs.environment)] }}
        username: ${{ secrets.DEPLOY_USER }}
        key: ${{ secrets.DEPLOY_SSH_KEY }}
        script: |
          cd /opt/flask-app
          docker-compose pull
          docker tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.event.inputs.version }} flask-app:latest
          docker-compose up -d
          docker-compose exec -T app flask db upgrade
```

**Step 6: Test CI workflow locally**

```bash
# Install act (GitHub Actions local runner)
# brew install act  # macOS
# or download from https://github.com/nektos/act

# Run CI workflow locally
act push

# Run specific job
act -j test
```

**Step 7: Commit**

```bash
git add .github/
git add docs/github-secrets.md
git commit -m "feat: add GitHub Actions CI/CD workflows"
```

**Step 8: Push and verify**

```bash
git push origin main

# Check Actions tab in GitHub
```

---

## Task 22: API Versioning

**Files:**
- Create: `app/api/v1/__init__.py`
- Create: `app/api/v2/__init__.py`
- Modify: `app/__init__.py`
- Create: `app/utils/versioning.py`

**Step 1: Create app/api/v1/__init__.py**

```python
"""API v1."""
from flask_restx import Api

# Import v1 namespaces
from app.api.health import api as health_ns
from app.schemas.auth import api as auth_ns
from app.schemas.user import api as users_ns

# Create API v1
api_v1 = Api(
    version='1.0',
    title='Flask REST API v1',
    description='Version 1 of the Flask REST API',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    security='Bearer'
)

# Register v1 namespaces
api_v1.add_namespace(health_ns, path='/health')
api_v1.add_namespace(auth_ns, path='/auth')
api_v1.add_namespace(users_ns, path='/users')
```

**Step 2: Create app/api/v2/__init__.py**

```python
"""
API v2 with improvements.

Changes from v1:
- Enhanced response format with metadata
- Improved error messages
- Additional endpoints
"""
from flask_restx import Api

# Import v2 namespaces (can have breaking changes from v1)
from app.api.health import api as health_ns
from app.schemas.auth import api as auth_ns
from app.schemas.user import api as users_ns

# Create API v2
api_v2 = Api(
    version='2.0',
    title='Flask REST API v2',
    description='Version 2 of the Flask REST API with improvements and breaking changes',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    security='Bearer'
)

# Register v2 namespaces
api_v2.add_namespace(health_ns, path='/health')
api_v2.add_namespace(auth_ns, path='/auth')
api_v2.add_namespace(users_ns, path='/users')

# V2 can have additional namespaces or modified implementations
```

**Step 3: Create app/utils/versioning.py**

```python
"""API versioning utilities."""
from functools import wraps
from flask import request, jsonify


def api_version_required(min_version='1.0', max_version='2.0'):
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
            # Get version from header
            version = request.headers.get('API-Version', '1.0')

            try:
                version_float = float(version)
                min_float = float(min_version)
                max_float = float(max_version)

                if version_float < min_float or version_float > max_float:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'UNSUPPORTED_API_VERSION',
                            'message': f'API version {version} not supported',
                            'supported_versions': f'{min_version} - {max_version}'
                        }
                    }), 400

            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_API_VERSION',
                        'message': f'Invalid API version format: {version}'
                    }
                }), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_api_version():
    """Get API version from request header."""
    return request.headers.get('API-Version', '1.0')


def is_version_compatible(version, target_version):
    """Check if API version is compatible."""
    try:
        return float(version) >= float(target_version)
    except ValueError:
        return False
```

**Step 4: Update app/__init__.py for versioning**

```python
from flask import Flask, Blueprint, jsonify
from app.api.v1 import api_v1
from app.api.v2 import api_v2

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions...
    # ... existing initialization code ...

    # Create blueprints for each API version
    blueprint_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    api_v1.init_app(blueprint_v1)
    app.register_blueprint(blueprint_v1)

    blueprint_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')
    api_v2.init_app(blueprint_v2)
    app.register_blueprint(blueprint_v2)

    # API root endpoint
    @app.route('/api')
    def api_root():
        """API version information."""
        return jsonify({
            'name': 'Flask REST API',
            'versions': {
                'v1': {
                    'url': '/api/v1',
                    'docs': '/api/v1/docs',
                    'status': 'stable'
                },
                'v2': {
                    'url': '/api/v2',
                    'docs': '/api/v2/docs',
                    'status': 'stable'
                }
            },
            'default_version': 'v1',
            'latest_version': 'v2'
        })

    # Default route redirects to latest docs
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Flask REST API',
            'documentation': '/api'
        })

    return app
```

**Step 5: Create version-specific modifications** (example)

Create `app/api/v2/users.py` for V2-specific changes:

```python
"""Users API v2 with enhanced responses."""
from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required
from app.schemas.user import api, user_model
from app.services.user_service import UserService


@api.route('')
class UserListV2(Resource):
    """User list resource (v2)."""

    @jwt_required()
    @api.response(200, 'Success')
    def get(self):
        """
        Get list of users with enhanced v2 response format.

        V2 changes:
        - Added metadata section
        - Improved pagination info
        - Response timing information
        """
        import time
        start_time = time.time()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        result = UserService.get_users(page=page, per_page=per_page)

        # V2 enhanced response format
        return {
            'success': True,
            'data': result['users'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'pages': result['pages']
            },
            'metadata': {
                'version': '2.0',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        }, 200
```

**Step 6: Add version deprecation warning**

Create `app/middleware/version_deprecation.py`:

```python
"""API version deprecation middleware."""
from flask import request, g
import warnings


def check_version_deprecation():
    """Check for deprecated API versions."""
    version = request.headers.get('API-Version', '1.0')

    # Warn about old versions
    if version < '1.0':
        warnings.warn(
            f'API version {version} is deprecated and will be removed',
            DeprecationWarning
        )
        g.deprecated_version = True
```

**Step 7: Create API version migration guide**

Create `docs/api-version-migration.md`:

```markdown
# API Version Migration Guide

## v1 to v2 Migration

### Breaking Changes

1. **Response Format**
   - V1: Simple data wrapper
   - V2: Enhanced with metadata and pagination object

2. **Error Codes**
   - V2 uses more specific error codes
   - Error messages are more detailed

3. **Date Format**
   - V1: ISO 8601 basic format
   - V2: ISO 8601 with timezone

### Migrating Your Code

#### Before (v1):
```python
response = requests.get('http://api/v1/users')
data = response.json()
users = data['users']
```

#### After (v2):
```python
response = requests.get('http://api/v2/users')
data = response.json()
users = data['data']  # Changed key name
pagination = data['pagination']  # New pagination object
```

### Deprecation Timeline

- v1.0: Stable, supported until 2026-12-31
- v2.0: Current stable version
```

**Step 8: Test API versioning**

```bash
# V1 API
curl http://localhost:5000/api/v1/health

# V2 API
curl http://localhost:5000/api/v2/health

# Version info
curl http://localhost:5000/api
```

**Step 9: Commit**

```bash
git add app/api/v1/ app/api/v2/ app/utils/versioning.py docs/api-version-migration.md
git commit -m "feat: add API versioning support (v1 and v2)"
```

---

## Task 23: Pagination with Link Headers

**Files:**
- Create: `app/utils/pagination.py`
- Modify: `app/services/user_service.py`
- Modify: `app/api/users.py`

**Step 1: Create app/utils/pagination.py**

```python
"""Pagination utilities with HATEOAS support."""
from flask import request, url_for
from urllib.parse import urlencode


def generate_pagination_links(pagination, endpoint, **kwargs):
    """
    Generate pagination links (RFC 5988).

    Returns Link header with first, prev, next, last links.

    Args:
        pagination: SQLAlchemy pagination object
        endpoint: Flask endpoint name
        **kwargs: Additional URL parameters

    Returns:
        str: Link header value
    """
    links = []

    # Build query params
    params = {k: v for k, v in kwargs.items() if v is not None}

    # First page
    first_params = {**params, 'page': 1}
    links.append(f'<{_build_url(endpoint, **first_params)}>; rel="first"')

    # Previous page
    if pagination.has_prev:
        prev_params = {**params, 'page': pagination.prev_num}
        links.append(f'<{_build_url(endpoint, **prev_params)}>; rel="prev"')

    # Next page
    if pagination.has_next:
        next_params = {**params, 'page': pagination.next_num}
        links.append(f'<{_build_url(endpoint, **next_params)}>; rel="next"')

    # Last page
    last_params = {**params, 'page': pagination.pages}
    links.append(f'<{_build_url(endpoint, **last_params)}>; rel="last"')

    return ', '.join(links)


def _build_url(endpoint, **params):
    """Build URL with query parameters."""
    base_url = url_for(endpoint, _external=True)
    query_string = urlencode({k: v for k, v in params.items() if v is not None})
    return f'{base_url}?{query_string}' if query_string else base_url


def paginate_response(pagination, data, endpoint, **kwargs):
    """
    Create HATEOAS paginated response.

    Args:
        pagination: SQLAlchemy pagination object
        data: List of data items
        endpoint: Flask endpoint name
        **kwargs: Additional URL parameters

    Returns:
        dict: Paginated response with HATEOAS links
    """
    params = {k: v for k, v in kwargs.items() if v is not None}
    params['per_page'] = pagination.per_page

    return {
        'data': data,
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        },
        'links': {
            'self': _build_url(endpoint, page=pagination.page, **params),
            'first': _build_url(endpoint, page=1, **params),
            'last': _build_url(endpoint, page=pagination.pages, **params),
            'next': _build_url(endpoint, page=pagination.next_num, **params) if pagination.has_next else None,
            'prev': _build_url(endpoint, page=pagination.prev_num, **params) if pagination.has_prev else None,
        }
    }


class Pagination:
    """Custom pagination class with additional utilities."""

    def __init__(self, query, page, per_page, total, items):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        """Total number of pages."""
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self):
        """True if there is a previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """True if there is a next page."""
        return self.page < self.pages

    @property
    def prev_num(self):
        """Previous page number."""
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        """Next page number."""
        return self.page + 1 if self.has_next else None

    def to_dict(self):
        """Convert pagination to dictionary."""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num,
        }
```

**Step 2: Update app/services/user_service.py**

```python
from app.models.user import User

class UserService:
    @staticmethod
    def get_users(page=1, per_page=10):
        """
        Get paginated list of users.

        Returns pagination object instead of dict.
        """
        pagination = User.query.filter_by(is_active=True).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return pagination
```

**Step 3: Update app/api/users.py**

```python
from flask import make_response, jsonify
from flask_restx import Resource
from flask_jwt_extended import jwt_required
from app.schemas.user import api
from app.services.user_service import UserService
from app.utils.pagination import generate_pagination_links, paginate_response


@api.route('')
class UserList(Resource):
    """User list resource with pagination."""

    @jwt_required()
    @api.response(200, 'Success')
    @api.doc(params={
        'page': {'description': 'Page number', 'type': 'integer', 'default': 1},
        'per_page': {'description': 'Items per page', 'type': 'integer', 'default': 10}
    })
    def get(self):
        """
        Get list of users with pagination and Link headers.

        Returns paginated user list with HATEOAS links in both
        response body and Link header (RFC 5988).
        """
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Validate pagination parameters
        if page < 1:
            api.abort(400, 'Page must be >= 1')
        if per_page < 1 or per_page > 100:
            api.abort(400, 'Per page must be between 1 and 100')

        # Get paginated users
        pagination = UserService.get_users(page=page, per_page=per_page)
        users_data = [user.to_dict() for user in pagination.items]

        # Create HATEOAS response
        response_data = paginate_response(
            pagination,
            users_data,
            'api_v1.users_user_list',  # Adjust based on blueprint name
            per_page=per_page
        )

        # Create response with Link header
        response = make_response(jsonify(response_data), 200)

        # Add Link header (RFC 5988)
        link_header = generate_pagination_links(
            pagination,
            'api_v1.users_user_list',
            per_page=per_page
        )
        response.headers['Link'] = link_header

        # Add custom pagination headers
        response.headers['X-Total-Count'] = str(pagination.total)
        response.headers['X-Page'] = str(pagination.page)
        response.headers['X-Per-Page'] = str(pagination.per_page)
        response.headers['X-Total-Pages'] = str(pagination.pages)

        return response
```

**Step 4: Create pagination helper for other endpoints**

Update `app/utils/__init__.py`:

```python
from app.utils.pagination import (
    generate_pagination_links,
    paginate_response,
    Pagination
)

__all__ = [
    'setup_logging',
    'cached',
    'invalidate_cache',
    'generate_pagination_links',
    'paginate_response',
    'Pagination'
]
```

**Step 5: Test pagination**

```bash
# Start app
flask run

# Test pagination
curl -H "Authorization: Bearer <token>" \
     "http://localhost:5000/api/v1/users?page=1&per_page=5" \
     -v

# Check response headers for Link header
```

Expected output:
```
< HTTP/1.1 200 OK
< Content-Type: application/json
< Link: <http://localhost:5000/api/v1/users?page=1&per_page=5>; rel="first", <http://localhost:5000/api/v1/users?page=2&per_page=5>; rel="next", <http://localhost:5000/api/v1/users?page=3&per_page=5>; rel="last"
< X-Total-Count: 15
< X-Page: 1
< X-Per-Page: 5
< X-Total-Pages: 3
```

**Step 6: Create pagination documentation**

Create `docs/pagination.md`:

```markdown
# API Pagination Guide

## Overview

All list endpoints support pagination using query parameters.

## Query Parameters

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)

## Response Format

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "self": "http://api/users?page=1",
    "first": "http://api/users?page=1",
    "next": "http://api/users?page=2",
    "last": "http://api/users?page=10"
  }
}
```

## HTTP Headers

### Response Headers

- `Link`: RFC 5988 pagination links
- `X-Total-Count`: Total number of items
- `X-Page`: Current page number
- `X-Per-Page`: Items per page
- `X-Total-Pages`: Total number of pages

### Link Header Format

```
Link: <url>; rel="first", <url>; rel="prev", <url>; rel="next", <url>; rel="last"
```

## Example Usage

### cURL

```bash
curl -H "Authorization: Bearer token" \
     "http://api/users?page=2&per_page=20"
```

### Python

```python
import requests

response = requests.get(
    'http://api/users',
    params={'page': 2, 'per_page': 20},
    headers={'Authorization': 'Bearer token'}
)

data = response.json()
users = data['data']
meta = data['meta']
links = data['links']

# Get next page
if links['next']:
    next_response = requests.get(links['next'])
```

### JavaScript

```javascript
const response = await fetch('http://api/users?page=1&per_page=10', {
  headers: { 'Authorization': 'Bearer token' }
});

const data = await response.json();
const users = data.data;
const pagination = data.meta;

// Parse Link header
const linkHeader = response.headers.get('Link');
```
```

**Step 7: Add pagination tests**

Create `tests/test_pagination.py`:

```python
"""Pagination tests."""


def test_users_pagination(client, auth_headers, db_session):
    """Test users pagination."""
    # Create test users
    from app.models.user import User
    for i in range(25):
        user = User(
            email=f'user{i}@test.com',
            first_name='Test',
            last_name=f'User{i}'
        )
        user.set_password('password')
        user.save()

    # Test first page
    response = client.get('/api/users?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200

    data = response.json
    assert len(data['data']) == 10
    assert data['meta']['page'] == 1
    assert data['meta']['total'] >= 25
    assert data['links']['next'] is not None

    # Check Link header
    link_header = response.headers.get('Link')
    assert link_header is not None
    assert 'rel="next"' in link_header


def test_pagination_validation(client, auth_headers):
    """Test pagination parameter validation."""
    # Invalid page
    response = client.get('/api/users?page=0', headers=auth_headers)
    assert response.status_code == 400

    # Invalid per_page
    response = client.get('/api/users?per_page=101', headers=auth_headers)
    assert response.status_code == 400
```

**Step 8: Commit**

```bash
git add app/utils/pagination.py docs/pagination.md tests/test_pagination.py
git commit -m "feat: add pagination with Link headers and HATEOAS"
```

---

## Task 24: Flower Dashboard for Celery

**Files:**
- Modify: `requirements.txt`
- Modify: `docker-compose.yml`
- Create: `flower_config.py`
- Modify: `docker/nginx.conf`
- Modify: `.env.example`

**Step 1: Add Flower dependency**

```txt
flower==2.0.1
```

**Step 2: Create flower_config.py**

```python
"""Flower configuration."""
import os

# Celery broker URL
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')

# Flower basic authentication
basic_auth = [
    os.getenv('FLOWER_USER', 'admin') + ':' + os.getenv('FLOWER_PASSWORD', 'change_me')
]

# Port
port = int(os.getenv('FLOWER_PORT', '5555'))

# URL prefix for reverse proxy
url_prefix = os.getenv('FLOWER_URL_PREFIX', '')

# Persistent storage
persistent = True
db = os.getenv('FLOWER_DB', 'flower.db')

# Max tasks to keep in memory
max_tasks = int(os.getenv('FLOWER_MAX_TASKS', '10000'))

# Enable events
enable_events = True

# Purge offline workers
purge_offline_workers = int(os.getenv('FLOWER_PURGE_OFFLINE_WORKERS', '60'))

# Auto-refresh interval (seconds)
auto_refresh = True
```

**Step 3: Update docker-compose.yml**

Add Flower service:

```yaml
  flower:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: flask_flower
    restart: unless-stopped
    command: celery -A celery_worker.celery flower --conf=flower_config
    env_file:
      - .env
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - FLOWER_USER=${FLOWER_USER:-admin}
      - FLOWER_PASSWORD=${FLOWER_PASSWORD:-change_me}
      - FLOWER_PORT=5555
      - FLOWER_URL_PREFIX=/flower
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery_worker
    networks:
      - backend
    volumes:
      - flower_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5555/api/workers"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Add volume:

```yaml
volumes:
  mysql_data:
  redis_data:
  flower_data:  # Add this
```

**Step 4: Update docker/nginx.conf**

Add Flower proxy:

```nginx
# Flower dashboard
location /flower/ {
    proxy_pass http://flower:5555/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support for Flower
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Basic auth (optional if Flower has its own)
    # auth_basic "Flower Dashboard";
    # auth_basic_user_file /etc/nginx/.htpasswd;
}

# Flower API (optional)
location /flower/api/ {
    proxy_pass http://flower:5555/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Step 5: Update .env.example**

```bash
# Flower Dashboard
FLOWER_USER=admin
FLOWER_PASSWORD=secure_password_here
FLOWER_PORT=5555
FLOWER_URL_PREFIX=/flower
FLOWER_MAX_TASKS=10000
FLOWER_PURGE_OFFLINE_WORKERS=60
```

**Step 6: Create Flower authentication helper**

Create `app/utils/flower_auth.py`:

```python
"""Flower authentication utilities."""
import os
from functools import wraps
from flask import request, Response


def check_flower_credentials(username, password):
    """Verify Flower credentials."""
    expected_user = os.getenv('FLOWER_USER', 'admin')
    expected_pass = os.getenv('FLOWER_PASSWORD', 'change_me')
    return username == expected_user and password == expected_pass


def require_flower_auth(f):
    """Decorator to require authentication for Flower-related endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization

        if not auth or not check_flower_credentials(auth.username, auth.password):
            return Response(
                'Authentication required for Flower dashboard',
                401,
                {'WWW-Authenticate': 'Basic realm="Flower Dashboard"'}
            )

        return f(*args, **kwargs)
    return decorated_function
```

**Step 7: Add Flower info endpoint** (optional)

Create `app/api/celery.py`:

```python
"""Celery monitoring API."""
from flask import current_app
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.extensions import celery

api = Namespace('celery', description='Celery monitoring')


@api.route('/stats')
class CeleryStats(Resource):
    """Celery statistics."""

    @jwt_required()
    @api.response(200, 'Success')
    def get(self):
        """Get Celery worker statistics."""
        try:
            inspect = celery.control.inspect()

            stats = {
                'active_workers': len(inspect.active() or {}),
                'active_tasks': sum(len(tasks) for tasks in (inspect.active() or {}).values()),
                'scheduled_tasks': sum(len(tasks) for tasks in (inspect.scheduled() or {}).values()),
                'registered_tasks': list((inspect.registered() or {}).values())[0] if inspect.registered() else [],
                'flower_dashboard': '/flower'
            }

            return {
                'success': True,
                'data': stats
            }, 200

        except Exception as e:
            current_app.logger.error(f'Failed to get Celery stats: {e}')
            api.abort(500, 'Failed to retrieve Celery statistics')
```

**Step 8: Test Flower**

```bash
# Start all services
docker-compose up -d

# Check Flower is running
docker-compose ps flower

# Access Flower dashboard
open http://localhost:5555

# Or through Nginx
open http://localhost/flower
```

Login with credentials from `.env`:
- Username: admin
- Password: change_me

**Step 9: Create Flower usage documentation**

Create `docs/flower-dashboard.md`:

```markdown
# Flower Dashboard Guide

## Overview

Flower is a real-time web-based monitoring tool for Celery.

## Access

### Local Development
- Direct: http://localhost:5555
- Through Nginx: http://localhost/flower

### Production
- https://yourdomain.com/flower

## Authentication

Default credentials (change in production):
- Username: admin
- Password: Set via `FLOWER_PASSWORD` environment variable

## Features

### Tasks
- View all executed tasks
- Task results and exceptions
- Task execution time
- Task arguments and kwargs
- Task state (PENDING, STARTED, SUCCESS, FAILURE, etc.)

### Workers
- Active workers list
- Worker statistics
- Worker configuration
- Pool information

### Monitor
- Real-time task monitoring
- Task execution graph
- Success/failure rates
- Task processing time

### Broker
- Queue lengths
- Message rates
- Connection information

## API Access

Flower provides a REST API:

```bash
# Get workers
curl http://localhost:5555/api/workers

# Get tasks
curl http://localhost:5555/api/tasks

# Get task info
curl http://localhost:5555/api/task/info/{task-id}
```

## Configuration

See `flower_config.py` for configuration options:

- `broker_url`: Celery broker URL
- `basic_auth`: Authentication credentials
- `port`: Server port
- `max_tasks`: Maximum tasks to keep in memory
- `purge_offline_workers`: Purge workers offline for X seconds

## Security

### Production Recommendations

1. **Strong Password**: Change default password
2. **HTTPS Only**: Use SSL/TLS in production
3. **IP Whitelist**: Restrict access by IP
4. **VPN**: Access only through VPN

### Nginx Authentication

Add to `nginx.conf`:

```nginx
location /flower/ {
    auth_basic "Flower Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... rest of config
}
```

Create `.htpasswd`:

```bash
htpasswd -c /etc/nginx/.htpasswd admin
```

## Troubleshooting

### Flower Not Starting

```bash
# Check logs
docker-compose logs flower

# Check Celery connection
docker-compose exec flower celery -A celery_worker.celery inspect ping
```

### No Workers Visible

- Ensure celery_worker service is running
- Check broker connection
- Verify Redis is accessible

### Authentication Issues

- Check `FLOWER_USER` and `FLOWER_PASSWORD` in `.env`
- Clear browser cookies
- Check Flower logs for auth errors
```

**Step 10: Commit**

```bash
git add flower_config.py docker-compose.yml docker/nginx.conf docs/flower-dashboard.md
git commit -m "feat: add Flower dashboard for Celery monitoring"
```

---

## Enhancement Implementation Complete!

All 9 optional enhancements (Tasks 16-24) are now fully documented:

✅ **Task 16**: OAuth2 Social Login (Google)
✅ **Task 17**: WebSocket Real-time Features
✅ **Task 18**: Redis Caching Decorator
✅ **Task 19**: Prometheus Metrics
✅ **Task 20**: Sentry Error Tracking
✅ **Task 21**: GitHub Actions CI/CD
✅ **Task 22**: API Versioning (v1/v2)
✅ **Task 23**: Pagination with Link Headers
✅ **Task 24**: Flower Dashboard for Celery

## Implementation Order Recommendation

1. **Essential First**: Tasks 18-20 (Caching, Metrics, Error Tracking)
2. **DevOps Next**: Task 21 (CI/CD)
3. **API Improvements**: Tasks 22-23 (Versioning, Pagination)
4. **Additional Features**: Tasks 16-17, 24 (OAuth, WebSocket, Flower)

## Quick Start

```bash
# Install all enhancement dependencies
pip install -r requirements.txt

# Run with all features
docker-compose up -d

# Access dashboards
open http://localhost/api/docs        # Swagger UI
open http://localhost/flower          # Flower Dashboard
open http://localhost/metrics         # Prometheus Metrics
```

## Testing Enhancements

```bash
# Run all tests
pytest -v --cov=app

# Test specific enhancements
pytest tests/test_cache.py -v
pytest tests/test_pagination.py -v

# Check CI locally
act -j test
```

---

**Plan saved to:** `docs/plans/2026-01-09-flask-enhancements.md`
