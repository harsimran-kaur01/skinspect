import pytest
from fastapi.testclient import TestClient
from app.main import app
from .conftest import client, setup_test_db, test_user, auth_token, auth_user


def test_register():
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert "access_token" in data["token"]


def test_register_duplicate_email():
    """Test registration with duplicate email."""
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "TestPassword123"},
    )

    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "AnotherPassword123"},
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_invalid_email():
    """Test registration with invalid email."""
    response = client.post(
        "/api/auth/register",
        json={"email": "invalid-email", "password": "TestPassword123"},
    )
    assert response.status_code == 422


def test_register_weak_password():
    """Test registration with weak password."""
    response = client.post(
        "/api/auth/register", json={"email": "test@example.com", "password": "weak"}
    )
    assert response.status_code == 422


def test_login():
    """Test user login."""
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "TestPassword123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert "access_token" in data["token"]


def test_login_wrong_password():
    """Test login with wrong password."""
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "TestPassword123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Test login with nonexistent user."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 401


def test_get_me(auth_token):
    """Test getting current user profile."""
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_me_unauthorized():
    """Test getting profile without token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token():
    """Test getting profile with invalid token."""
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_update_me(auth_token):
    """Test updating user profile."""
    response = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_patch_me(auth_token):
    """Test partially updating user profile."""
    response = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"full_name": "Patched Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Patched Name"


def test_update_me_email(auth_token):
    """Test updating user email."""
    response = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"email": "newemail@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


def test_logout(auth_token):
    """Test logout."""
    response = client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_delete_account(auth_token, auth_user):
    """Test deleting user account."""
    response = client.delete(
        "/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204
