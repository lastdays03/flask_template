"""Authentication API tests."""
import pytest


def test_register_success(client, db_session):
    """Test successful user registration."""
    response = client.post('/api/v1/auth/register', json={
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
    response = client.post('/api/v1/auth/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    assert response.status_code == 400


def test_login_success(client, sample_user):
    """Test successful login."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data


def test_login_invalid_credentials(client, sample_user):
    """Test login with invalid credentials."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })

    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get('/api/v1/auth/me', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['email'] == 'test@example.com'


def test_unauthorized_access(client):
    """Test accessing protected endpoint without auth."""
    response = client.get('/api/v1/auth/me')

    assert response.status_code == 401
