"""Pytest configuration and fixtures."""

import sys
import os
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import User  # noqa: E402


class MockRedis:
    """Mock Redis client."""

    def __init__(self):
        self.store = {}

    def get(self, name):
        return self.store.get(name)

    def setex(self, name, time, value):
        self.store[name] = value

    def delete(self, name):
        if name in self.store:
            del self.store[name]


@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing."""
    application = create_app("testing")

    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    """Mock Redis client for all tests."""
    mock = MockRedis()
    with (
        patch("app.utils.cache.get_redis_client", return_value=mock),
        patch("app.utils.auth.get_redis_client", return_value=mock),
    ):
        yield mock


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        # Clean up before test
        User.query.delete()
        db.session.commit()

        yield db

        # Clean up after test
        db.session.rollback()


@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create sample user."""
    user = User(email="test@example.com", first_name="Test", last_name="User")
    user.set_password("StrongPass1!")
    user.save()
    return user


@pytest.fixture(scope="function")
def auth_headers(client, sample_user):
    """Get authentication headers."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongPass1!"},
    )

    data = response.get_json()
    access_token = data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}
