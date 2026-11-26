
"""
Authentication security utilities.

Features:
- Argon2 password hashing
- Password verification
- Short-lived JWT access tokens
- JWT refresh tokens
- Token type and expiry validation
"""

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.config import settings


password_hasher = PasswordHash.recommended()


class AuthSecurity:
    ISSUER = "production-rag-service"

    @staticmethod
    def _get_secret() -> str:
        secret = settings.JWT_SECRET_KEY

        if not secret or len(secret) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY must contain at least "
                "32 characters. Configure it in .env."
            )

        return secret

    @staticmethod
    def hash_password(password: str) -> str:
        """Store an Argon2 hash, never a plaintext password."""
        return password_hasher.hash(password)

    @staticmethod
    def verify_password(
        password: str,
        password_hash: str,
    ) -> bool:
        """Verify a password against its stored hash."""
        try:
            return password_hasher.verify(
                password,
                password_hash,
            )
        except (ValueError, TypeError):
            return False

    @classmethod
    def _create_token(
        cls,
        user_id: str,
        token_type: str,
        lifetime: timedelta,
    ) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        expires_at = now + lifetime

        payload = {
            "sub": user_id,
            "type": token_type,
            "iss": cls.ISSUER,
            "iat": now,
            "nbf": now,
            "exp": expires_at,
            "jti": secrets.token_urlsafe(24),
        }

        token = jwt.encode(
            payload,
            cls._get_secret(),
            algorithm=settings.JWT_ALGORITHM,
        )

        return token, int(expires_at.timestamp())

    @classmethod
    def create_access_token(
        cls,
        user_id: str,
    ) -> tuple[str, int]:
        """Create a short-lived access token."""
        return cls._create_token(
            user_id=user_id,
            token_type="access",
            lifetime=timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_MINUTES
            ),
        )

    @classmethod
    def create_refresh_token(
        cls,
        user_id: str,
    ) -> tuple[str, int]:
        """Create a longer-lived refresh token."""
        return cls._create_token(
            user_id=user_id,
            token_type="refresh",
            lifetime=timedelta(
                days=settings.JWT_REFRESH_TOKEN_DAYS
            ),
        )

    @classmethod
    def _verify_token(
        cls,
        token: str,
        expected_type: str,
    ) -> str | None:
        if not isinstance(token, str) or not token:
            return None

        try:
            payload = jwt.decode(
                token,
                cls._get_secret(),
                algorithms=[settings.JWT_ALGORITHM],
                issuer=cls.ISSUER,
                options={
                    "require": [
                        "sub",
                        "type",
                        "iss",
                        "iat",
                        "nbf",
                        "exp",
                        "jti",
                    ]
                },
                leeway=0,
            )

        except InvalidTokenError:
            return None

        user_id = payload.get("sub")

        if (
            payload.get("type") != expected_type
            or not isinstance(user_id, str)
            or not user_id.strip()
        ):
            return None

        return user_id

    @classmethod
    def verify_access_token(
        cls,
        token: str,
    ) -> str | None:
        """Return user ID for a valid access token."""
        return cls._verify_token(
            token,
            expected_type="access",
        )

    @classmethod
    def verify_refresh_token(
        cls,
        token: str,
    ) -> str | None:
        """Return user ID for a valid refresh token."""
        return cls._verify_token(
            token,
            expected_type="refresh",
        )

