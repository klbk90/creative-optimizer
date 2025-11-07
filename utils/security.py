"""
Security utilities for encryption and rate limiting.
"""

import os
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# Encryption for sensitive data (TikTok tokens, etc.)
# ============================================================================

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ cryptography not installed. Install with: pip install cryptography")
    ENCRYPTION_AVAILABLE = False


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""

    def __init__(self):
        self.cipher = None
        self._init_cipher()

    def _init_cipher(self):
        """Initialize encryption cipher."""
        if not ENCRYPTION_AVAILABLE:
            return

        # Get encryption key from environment
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            logger.warning(
                "⚠️ ENCRYPTION_KEY not set. Generate one with:\n"
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
            return

        try:
            self.cipher = Fernet(encryption_key.encode())
            logger.info("✅ Encryption service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption: {e}")

    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded) or None
        """
        if not self.cipher:
            # Fallback: return plaintext (not secure!)
            logger.warning("Encryption not available - storing plaintext")
            return plaintext

        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt encrypted string.

        Args:
            ciphertext: Encrypted string

        Returns:
            Decrypted string or None
        """
        if not self.cipher:
            # Fallback: assume it's plaintext
            return ciphertext

        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            # Might be plaintext if encryption was disabled before
            logger.debug(f"Decryption error (might be plaintext): {e}")
            return ciphertext


# Global encryption service
_encryption_service = None


def get_encryption() -> EncryptionService:
    """Get global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_token(token: str) -> str:
    """Helper to encrypt a token."""
    service = get_encryption()
    encrypted = service.encrypt(token)
    return encrypted if encrypted else token


def decrypt_token(encrypted_token: str) -> str:
    """Helper to decrypt a token."""
    service = get_encryption()
    decrypted = service.decrypt(encrypted_token)
    return decrypted if decrypted else encrypted_token


# ============================================================================
# Rate Limiting
# ============================================================================

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ slowapi not installed. Install with: pip install slowapi")
    RATE_LIMIT_AVAILABLE = False


def get_rate_limiter():
    """
    Create rate limiter instance.

    Returns:
        Limiter instance or None
    """
    if not RATE_LIMIT_AVAILABLE:
        logger.warning("Rate limiting not available")
        return None

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per hour"],
        storage_uri=os.getenv("REDIS_URL", "memory://"),
    )

    return limiter


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "utm_generate": "100 per hour",      # Link generation
    "utm_track": "1000 per hour",        # Click tracking (higher limit)
    "webhook": "500 per hour",           # Conversion webhooks
    "analytics": "200 per hour",         # Analytics queries
    "admin": "500 per hour",             # Admin operations
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit for endpoint type.

    Args:
        endpoint_type: Type of endpoint (utm_generate, utm_track, etc.)

    Returns:
        Rate limit string (e.g., "100 per hour")
    """
    return RATE_LIMITS.get(endpoint_type, "100 per hour")


# ============================================================================
# CORS Configuration
# ============================================================================

def get_cors_origins() -> list:
    """
    Get allowed CORS origins from environment.

    Returns:
        List of allowed origins
    """
    origins_str = os.getenv("ALLOWED_ORIGINS", "")

    if not origins_str:
        # Development default
        logger.warning("⚠️ ALLOWED_ORIGINS not set. Using development defaults.")
        return [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]

    # Parse comma-separated origins
    origins = [origin.strip() for origin in origins_str.split(",")]

    # Warn if wildcard is used
    if "*" in origins:
        logger.warning("⚠️ CORS wildcard (*) is enabled. Not recommended for production!")

    return origins


# ============================================================================
# API Key Authentication (optional)
# ============================================================================

def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate API key.

    Args:
        api_key: API key to validate

    Returns:
        True if valid
    """
    if not api_key:
        return False

    # Get valid API keys from environment
    valid_keys_str = os.getenv("API_KEYS", "")
    if not valid_keys_str:
        # No API keys configured - allow all (dev mode)
        logger.warning("⚠️ No API keys configured")
        return True

    valid_keys = [key.strip() for key in valid_keys_str.split(",")]
    return api_key in valid_keys


def generate_api_key() -> str:
    """
    Generate a random API key.

    Returns:
        Random API key string
    """
    import secrets
    return f"utm_{secrets.token_urlsafe(32)}"


# ============================================================================
# Security Headers
# ============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def get_security_headers() -> dict:
    """
    Get recommended security headers.

    Returns:
        Dict of security headers
    """
    return SECURITY_HEADERS.copy()
