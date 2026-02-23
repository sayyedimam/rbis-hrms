import pytest

def test_signup_validation(client):
    """Test signup with invalid password"""
    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "weak"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_login_invalid_credentials(client):
    """Test login with non-existent user"""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password123!"}
    )
    assert response.status_code == 401
