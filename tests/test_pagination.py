"""Pagination tests."""


def test_users_pagination(client, auth_headers, db_session):
    """Test users pagination."""
    # Create test users
    from app.models.user import User

    for i in range(25):
        user = User(
            email=f"pagetest{i}@test.com", first_name="Test", last_name=f"User{i}"
        )
        user.set_password("StrongPass1!")
        user.save()

    # Test first page
    response = client.get("/api/v1/users?page=1&per_page=10", headers=auth_headers)
    assert response.status_code == 200

    data = response.get_json()
    assert len(data["users"]) == 10
    assert data["page"] == 1
    assert data["total"] >= 25
    assert data["links"]["next"] is not None

    # Check Link header
    link_header = response.headers.get("Link")
    assert link_header is not None
    assert 'rel="next"' in link_header


def test_pagination_validation(client, auth_headers):
    """Test pagination parameter validation."""
    # Invalid page
    response = client.get("/api/v1/users?page=0", headers=auth_headers)
    assert response.status_code == 400

    # Invalid per_page
    response = client.get("/api/v1/users?per_page=101", headers=auth_headers)
    assert response.status_code == 400
