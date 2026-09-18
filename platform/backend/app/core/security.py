"""Password hashing (PBKDF2-HMAC-SHA256, stdlib-only so it runs on any
Python and any platform), JWT creation/verification and RBAC dependencies.

PBKDF2 with 600k iterations is a NIST-recommended KDF and avoids native
build issues for bcrypt/argon2 on new Python releases.
"""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import Forbidden, Unauthorized
from app.database import get_db
from app.models.user import User

_ITERATIONS = 600_000
_SALT_BYTES = 16

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return "$".join(
        [
            "pbkdf2_sha256",
            str(_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(dk).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, iterations, salt_b64, dk_b64 = encoded.split("$")
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(dk_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def _settings():
    from app.config import get_settings

    return get_settings()


def create_access_token(user: User) -> str:
    settings = _settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = _settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("Invalid token") from exc


# ---------------------------------------------------------------------------
# FastAPI dependencies / RBAC
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise Unauthorized("User is disabled or missing")
    return user


def get_user_from_token(token: str, db: Session) -> User:
    """Resolve a bearer token string to an active user (shared by both
    header-based and query-param-based auth)."""
    payload = decode_token(token)
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise Unauthorized("User is disabled or missing")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependency factory: returns a dependency that enforces role membership."""

    def _checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise Forbidden(f"Requires one of roles: {', '.join(roles)}")
        return user

    return _checker


def db_session() -> Session:
    yield from get_db()