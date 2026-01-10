"""
Integration tests for Authentication API
"""
import pytest


class TestAuthAPI:
    """Test /api/v1/auth endpoints"""

    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "username": "newuser"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password

    def test_register_duplicate_email(self, client, sample_user):
        """Test duplicate email rejection"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": sample_user.email,  # Same email as sample_user
                "password": "password123",
                "username": "duplicate"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client, sample_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data

    def test_get_current_user_unauthorized(self, client):
        """Test unauthorized access"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
