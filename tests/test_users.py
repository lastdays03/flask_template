"""User API tests."""
import pytest


def test_get_users_list(client, auth_headers, sample_user):
    """Test getting users list."""
    response = client.get('/api/v1/users', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    assert data['total'] >= 1


def test_get_user_detail(client, auth_headers, sample_user):
    """Test getting user detail."""
    response = client.get(f'/api/v1/users/{sample_user.id}', headers=auth_headers)

    assert response.status_code == 200
    assert 'email' in response.get_json()


def test_update_user(client, auth_headers, sample_user):
    """Test updating user."""
    response = client.put(
        f'/api/v1/users/{sample_user.id}',
        headers=auth_headers,
        json={'first_name': 'Updated'}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['first_name'] == 'Updated'


def test_delete_user(client, auth_headers, sample_user):
    """Test deleting user."""
    response = client.delete(
        f'/api/v1/users/{sample_user.id}',
        headers=auth_headers
    )

    assert response.status_code == 204


def test_get_nonexistent_user(client, auth_headers):
    """Test getting nonexistent user."""
    response = client.get('/api/v1/users/99999', headers=auth_headers)

    assert response.status_code == 404
