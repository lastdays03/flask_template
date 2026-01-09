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
