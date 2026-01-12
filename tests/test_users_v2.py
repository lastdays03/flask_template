"""User API v2 tests."""
import pytest


def test_get_users_list_v2(client, auth_headers, sample_user):
    """Test getting users list v2 with HATEOAS."""
    headers = {**auth_headers, 'API-Version': '2.0'}
    response = client.get('/api/v2/users', headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    
    # Check v2 response structure
    assert 'data' in data
    assert 'meta' in data  # Changed from pagination to meta
    assert 'metadata' in data
    assert 'links' in data
    assert data['success'] is True
    
    # Check HATEOAS links
    assert 'self' in data['links']
    assert 'first' in data['links']
    assert 'last' in data['links']
    
    # Check metadata
    assert data['metadata']['version'] == '2.0'
    assert 'response_time_ms' in data['metadata']
    
    # Check Headers
    assert 'Link' in response.headers
    assert 'X-Total-Count' in response.headers
    assert 'X-Page' in response.headers


def test_get_users_list_v2_pagination(client, auth_headers, sample_user):
    """Test v2 pagination parameters."""
    headers = {**auth_headers, 'API-Version': '2.0'}
    response = client.get(
        '/api/v2/users?page=1&per_page=5', 
        headers=headers
    )

    assert response.status_code == 200
    data = response.get_json()
    
    # Check meta (pagination info)
    assert data['meta']['page'] == 1
    assert data['meta']['per_page'] == 5
    assert len(data['data']) <= 5
