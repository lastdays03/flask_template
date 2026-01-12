
def test_get_users_list_v2_no_header(client, auth_headers):
    """Test getting users list v2 without header (should infer from path)."""
    # auth_headers does not have API-Version
    response = client.get('/api/v2/users', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['metadata']['version'] == '2.0'
