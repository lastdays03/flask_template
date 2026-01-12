"""API v1."""
from flask import Blueprint
from flask_restx import Api

from app.api.v1.health import api as health_ns
from app.api.v1.auth import api as auth_ns
from app.api.v1.users import api as users_ns
from app.api.v1.oauth import api as oauth_ns
from app.api.v1.metrics import api as metrics_ns

blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')

api = Api(
    blueprint,
    title='Flask REST API v1',
    version='1.0',
    description='API v1',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    security='Bearer'
)

api.add_namespace(health_ns, path='/health')
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(users_ns, path='/users')
api.add_namespace(oauth_ns, path='/oauth')
api.add_namespace(metrics_ns, path='/metrics')

# Register error handlers
from app.utils.error_handlers import register_api_error_handlers
register_api_error_handlers(api)
