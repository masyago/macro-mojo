import pytest

def test_index_ok(client):
    response = client.get("/")
    assert response.status_code == 200

def test_login_page_ok(client):
    response = client.get("/login/")
    return response.status_code == 200