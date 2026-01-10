"""
Unit tests for security utilities
"""
import pytest
from utils.security import hash_password, verify_password, create_jwt_token, decode_jwt_token


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password can be hashed"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20  # Hashed password should be longer

    def test_verify_password_correct(self):
        """Test correct password verification"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test incorrect password rejection"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test salt ensures different hashes"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Same password, different hashes (due to salt)
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_token(self):
        """Test JWT token creation"""
        payload = {"user_id": "123", "email": "test@example.com"}
        token = create_jwt_token(payload)

        assert isinstance(token, str)
        assert len(token) > 50  # JWT should be long

    def test_decode_token(self):
        """Test JWT token decoding"""
        payload = {"user_id": "123", "email": "test@example.com"}
        token = create_jwt_token(payload)

        decoded = decode_jwt_token(token)

        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Test invalid token rejection"""
        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):
            decode_jwt_token(invalid_token)

    def test_decode_expired_token(self):
        """Test expired token rejection"""
        # Create token with 0 expiration
        payload = {"user_id": "123"}
        token = create_jwt_token(payload, expires_minutes=-1)

        # Should raise exception when decoding
        with pytest.raises(Exception):
            decode_jwt_token(token)
