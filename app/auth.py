from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import HTTPException, Request, Response, status


ADMIN_USERNAME = "admin"
SESSION_COOKIE_NAME = "store_expiration_session"
SESSION_DURATION = timedelta(hours=4)


@dataclass(frozen=True)
class AuthSettings:
    admin_password: str
    session_secret: str
    admin_username: str = ADMIN_USERNAME


@dataclass(frozen=True)
class AuthSession:
    username: str
    expires_at: datetime


@lru_cache
def get_settings() -> AuthSettings:
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    session_secret = os.environ.get("SESSION_SECRET", "").strip()

    missing = []
    if not admin_password:
        missing.append("ADMIN_PASSWORD")
    if not session_secret:
        missing.append("SESSION_SECRET")

    if missing:
        raise RuntimeError(
            "필수 환경변수가 없습니다: " + ", ".join(missing)
        )

    return AuthSettings(
        admin_password=admin_password,
        session_secret=session_secret,
    )


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
    )
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", maxsplit=2)
    except ValueError:
        return False

    if algorithm != "scrypt":
        return False

    try:
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    actual_digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def ensure_admin_user(connection: sqlite3.Connection, settings: AuthSettings) -> None:
    row = connection.execute(
        """
        SELECT id, password_hash, is_active
        FROM users
        WHERE username = ?
        """,
        (settings.admin_username,),
    ).fetchone()

    if row is None:
        connection.execute(
            """
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 1)
            """,
            (
                settings.admin_username,
                hash_password(settings.admin_password),
            ),
        )
        return

    should_update_password = not verify_password(
        settings.admin_password,
        row["password_hash"],
    )
    should_activate = row["is_active"] != 1

    if should_update_password or should_activate:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, is_active = 1
            WHERE id = ?
            """,
            (
                hash_password(settings.admin_password),
                row["id"],
            ),
        )


def authenticate_user(
    connection: sqlite3.Connection,
    username: str,
    password: str,
) -> bool:
    row = connection.execute(
        """
        SELECT password_hash, is_active
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if row is None or row["is_active"] != 1:
        return False

    return verify_password(password, row["password_hash"])


def build_session_response(session: AuthSession | None) -> dict[str, object | None]:
    if session is None:
        return {
            "authenticated": False,
            "username": None,
            "expires_at": None,
        }

    return {
        "authenticated": True,
        "username": session.username,
        "expires_at": session.expires_at,
    }


def create_session_token(settings: AuthSettings, username: str) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + SESSION_DURATION
    payload = {
        "exp": int(expires_at.timestamp()),
        "sub": username,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_bytes = payload_json.encode("utf-8")
    encoded_payload = _urlsafe_b64encode(payload_bytes)
    signature = hmac.new(
        settings.session_secret.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}", expires_at


def read_session_from_request(
    request: Request,
    settings: AuthSettings,
) -> AuthSession | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        settings.session_secret.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(_urlsafe_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return None

    username = payload.get("sub")
    expires_at_ts = payload.get("exp")
    if not isinstance(username, str) or not isinstance(expires_at_ts, int):
        return None

    expires_at = datetime.fromtimestamp(expires_at_ts, UTC)
    if expires_at <= datetime.now(UTC):
        return None

    return AuthSession(username=username, expires_at=expires_at)


def require_authenticated_user(request: Request) -> AuthSession:
    settings = get_settings()
    session = read_session_from_request(request, settings)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    return session


def set_session_cookie(
    response: Response,
    settings: AuthSettings,
    username: str,
) -> AuthSession:
    token, expires_at = create_session_token(settings, username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return AuthSession(username=username, expires_at=expires_at)


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)
