"""
Advanced authentication algorithms with security optimizations.
Data-driven approach to authentication security and performance.
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum

import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.config import get_settings

settings = get_settings()


class AuthMethod(Enum):
    """Authentication methods supported."""
    API_KEY = "api_key"
    JWT = "jwt"
    NONE = "none"


@dataclass
class AuthResult:
    """Authentication result with detailed information."""
    success: bool
    user_id: Optional[str] = None
    user_type: Optional[str] = None
    rate_limit: int = 60
    features: list = None
    auth_method: AuthMethod = AuthMethod.NONE
    expires_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []


class SecureAPIKeyManager:
    """
    Secure API Key management with hashing and expiration.
    MVP implementation focusing on security fundamentals.
    """

    def __init__(self):
        self.salt_length = 32
        self.hash_iterations = 100000  # PBKDF2 iterations
        # In production, this would come from secure storage/database
        self._initialize_secure_keys()

    def _initialize_secure_keys(self):
        """Initialize secure API key storage."""
        # MVP: Secure hashed storage of API keys
        self.api_keys_db = {
            # Format: hashed_key -> {user_info, salt, created_at, expires_at}
            self._hash_api_key("ofc-solver-demo-key-2024", "demo_salt_123"): {
                "user_id": "demo_user",
                "user_type": "demo", 
                "rate_limit": 100,
                "features": ["basic_analysis", "game_management"],
                "salt": "demo_salt_123",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=90),
                "is_active": True
            },
            self._hash_api_key("ofc-solver-test-key-2024", "test_salt_456"): {
                "user_id": "test_user",
                "user_type": "test",
                "rate_limit": 1000, 
                "features": ["all"],
                "salt": "test_salt_456",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=365),
                "is_active": True
            }
        }
        
        # Reverse lookup for validation (hashed_key -> original_key for demo)
        # In production, this would not exist
        self._demo_keys = {
            "ofc-solver-demo-key-2024": "demo_salt_123",
            "ofc-solver-test-key-2024": "test_salt_456"
        }

    def _hash_api_key(self, api_key: str, salt: str) -> str:
        """
        Hash API key using PBKDF2 with salt.
        Constant-time comparison resistant to timing attacks.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=self.hash_iterations,
        )
        hashed = kdf.derive(api_key.encode())
        return hashlib.sha256(hashed).hexdigest()

    def validate_api_key(self, api_key: str) -> AuthResult:
        """
        Validate API key with constant-time comparison.
        Returns detailed authentication result.
        """
        if not api_key:
            return AuthResult(
                success=False,
                error_code="MISSING_API_KEY",
                error_message="API key is required"
            )

        # Try all known keys with constant-time comparison
        for hashed_key, key_info in self.api_keys_db.items():
            # Get salt for this key
            salt = key_info["salt"]
            candidate_hash = self._hash_api_key(api_key, salt)
            
            # Constant-time comparison to prevent timing attacks
            if hmac.compare_digest(candidate_hash, hashed_key):
                return self._validate_key_info(key_info)

        return AuthResult(
            success=False,
            error_code="INVALID_API_KEY", 
            error_message="Invalid API key"
        )

    def _validate_key_info(self, key_info: Dict[str, Any]) -> AuthResult:
        """Validate key information and check expiration."""
        current_time = datetime.now(timezone.utc)
        
        # Check if key is active
        if not key_info.get("is_active", False):
            return AuthResult(
                success=False,
                error_code="API_KEY_REVOKED",
                error_message="API key has been revoked"
            )
        
        # Check expiration
        expires_at = key_info.get("expires_at")
        if expires_at and current_time > expires_at:
            return AuthResult(
                success=False,
                error_code="API_KEY_EXPIRED",
                error_message="API key has expired"
            )

        return AuthResult(
            success=True,
            user_id=key_info["user_id"],
            user_type=key_info["user_type"],
            rate_limit=key_info["rate_limit"],
            features=key_info["features"],
            auth_method=AuthMethod.API_KEY,
            expires_at=expires_at
        )

    def generate_new_api_key(self, user_id: str, user_type: str, days_valid: int = 90) -> Tuple[str, str]:
        """
        Generate new secure API key with expiration.
        Returns (api_key, key_id) tuple.
        """
        # Generate cryptographically secure API key
        api_key = f"ofc-{secrets.token_urlsafe(32)}-{int(time.time())}"
        salt = secrets.token_urlsafe(24)
        hashed_key = self._hash_api_key(api_key, salt)
        
        # Key info
        key_info = {
            "user_id": user_id,
            "user_type": user_type,
            "rate_limit": self._get_default_rate_limit(user_type),
            "features": self._get_default_features(user_type),
            "salt": salt,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=days_valid),
            "is_active": True
        }
        
        # Store in database
        self.api_keys_db[hashed_key] = key_info
        
        return api_key, hashed_key

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        # Find and deactivate the key
        for hashed_key, key_info in self.api_keys_db.items():
            salt = key_info["salt"]
            candidate_hash = self._hash_api_key(api_key, salt)
            
            if hmac.compare_digest(candidate_hash, hashed_key):
                key_info["is_active"] = False
                return True
        
        return False

    def _get_default_rate_limit(self, user_type: str) -> int:
        """Get default rate limit for user type."""
        limits = {
            "demo": 100,
            "basic": 200,
            "premium": 500,
            "enterprise": 1000,
            "test": 2000
        }
        return limits.get(user_type, 60)

    def _get_default_features(self, user_type: str) -> list:
        """Get default features for user type."""
        features = {
            "demo": ["basic_analysis", "game_management"],
            "basic": ["basic_analysis", "game_management", "training"],
            "premium": ["all"],
            "enterprise": ["all"],
            "test": ["all"]
        }
        return features.get(user_type, ["basic_analysis"])


class JWTManager:
    """
    JWT token management with RS256 support.
    Production-ready implementation with security best practices.
    """

    def __init__(self):
        self.algorithm = "RS256"  # More secure than HS256
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        # In production, load from secure key management
        self._load_keys()

    def _load_keys(self):
        """Load RSA keys for JWT signing."""
        # MVP: Generate keys on startup (in production, load from secure storage)
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        self.public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def create_access_token(self, user_id: str, user_type: str, features: list) -> str:
        """Create JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "user_type": user_type,
            "features": features,
            "iat": now,
            "exp": expire,
            "type": "access"
        }
        
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> AuthResult:
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            
            # Validate token type
            if payload.get("type") != "access":
                return AuthResult(
                    success=False,
                    error_code="INVALID_TOKEN_TYPE",
                    error_message="Invalid token type"
                )
            
            return AuthResult(
                success=True,
                user_id=payload["sub"],
                user_type=payload.get("user_type", "basic"),
                features=payload.get("features", []),
                auth_method=AuthMethod.JWT,
                expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc)
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_code="TOKEN_EXPIRED",
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            return AuthResult(
                success=False,
                error_code="INVALID_TOKEN",
                error_message=f"Invalid token: {str(e)}"
            )

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.public_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload["sub"]
            # In production, fetch user info from database
            user_type = "basic"  # MVP default
            features = ["basic_analysis"]  # MVP default
            
            new_access_token = self.create_access_token(user_id, user_type, features)
            new_refresh_token = self.create_refresh_token(user_id)
            
            return new_access_token, new_refresh_token
            
        except jwt.InvalidTokenError:
            return None


class AuthenticationService:
    """
    Unified authentication service.
    Handles both API Key and JWT authentication with performance monitoring.
    """

    def __init__(self):
        self.api_key_manager = SecureAPIKeyManager()
        self.jwt_manager = JWTManager()
        self.auth_metrics = {
            "total_requests": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "api_key_auths": 0,
            "jwt_auths": 0,
            "last_reset": time.time()
        }

    async def authenticate(self, api_key: Optional[str] = None, jwt_token: Optional[str] = None) -> AuthResult:
        """
        Authenticate request using available credentials.
        Returns comprehensive authentication result.
        """
        start_time = time.time()
        self.auth_metrics["total_requests"] += 1
        
        try:
            # Try JWT first (more secure)
            if jwt_token:
                result = self.jwt_manager.validate_token(jwt_token)
                if result.success:
                    self.auth_metrics["successful_auths"] += 1
                    self.auth_metrics["jwt_auths"] += 1
                    return result
            
            # Try API Key
            if api_key:
                result = self.api_key_manager.validate_api_key(api_key)
                if result.success:
                    self.auth_metrics["successful_auths"] += 1
                    self.auth_metrics["api_key_auths"] += 1
                    return result
            
            # No valid authentication provided
            self.auth_metrics["failed_auths"] += 1
            return AuthResult(
                success=False,
                error_code="NO_AUTHENTICATION",
                error_message="No valid authentication provided"
            )
            
        except Exception as e:
            self.auth_metrics["failed_auths"] += 1
            return AuthResult(
                success=False,
                error_code="AUTH_SERVICE_ERROR",
                error_message=f"Authentication service error: {str(e)}"
            )
        finally:
            # Record response time for monitoring
            response_time = time.time() - start_time
            # In production, send to monitoring system

    def get_auth_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics for monitoring."""
        current_time = time.time()
        elapsed_time = current_time - self.auth_metrics["last_reset"]
        
        return {
            "total_requests": self.auth_metrics["total_requests"],
            "successful_auths": self.auth_metrics["successful_auths"],
            "failed_auths": self.auth_metrics["failed_auths"],
            "success_rate": (
                self.auth_metrics["successful_auths"] / max(1, self.auth_metrics["total_requests"])
            ),
            "api_key_usage": self.auth_metrics["api_key_auths"],
            "jwt_usage": self.auth_metrics["jwt_auths"],
            "requests_per_minute": self.auth_metrics["total_requests"] / max(1, elapsed_time / 60),
            "uptime_seconds": elapsed_time
        }

    def reset_metrics(self):
        """Reset authentication metrics."""
        self.auth_metrics = {
            "total_requests": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "api_key_auths": 0,
            "jwt_auths": 0,
            "last_reset": time.time()
        }


# Global authentication service instance
auth_service = AuthenticationService()


def get_auth_service() -> AuthenticationService:
    """Get the authentication service instance."""
    return auth_service