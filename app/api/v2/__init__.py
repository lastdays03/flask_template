"""API v2."""
from flask import Blueprint
from flask_restx import Api
from app.api.v2.users import api as users_ns

blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')

api = Api(
    blueprint,
    title='Flask REST API v2',
    version='2.0',
    description='API v2',
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

api.add_namespace(users_ns, path='/users')
