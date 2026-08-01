from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


DEVELOPMENT = "development"
PRODUCTION = "production"
DEFAULT_APP_ENV = DEVELOPMENT
DEFAULT_DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


@dataclass(frozen=True)
class RuntimeSettings:
    app_env: str
    cors_allow_origins: tuple[str, ...]
    session_cookie_secure: bool
    api_docs_enabled: bool

    @property
    def is_production(self) -> bool:
        return self.app_env == PRODUCTION


@lru_cache
def get_runtime_settings() -> RuntimeSettings:
    app_env = _read_app_env()
    is_production = app_env == PRODUCTION

    return RuntimeSettings(
        app_env=app_env,
        cors_allow_origins=_read_cors_allow_origins(app_env),
        session_cookie_secure=_read_bool(
            "SESSION_COOKIE_SECURE",
            default=is_production,
        ),
        api_docs_enabled=_read_bool(
            "API_DOCS_ENABLED",
            default=not is_production,
        ),
    )


def _read_app_env() -> str:
    app_env = os.environ.get("APP_ENV", DEFAULT_APP_ENV).strip().lower()
    if app_env in {DEVELOPMENT, PRODUCTION}:
        return app_env

    raise RuntimeError(
        "APP_ENV must be one of: development, production"
    )


def _read_cors_allow_origins(app_env: str) -> tuple[str, ...]:
    configured_origins = os.environ.get("CORS_ALLOW_ORIGINS")
    if configured_origins is None:
        if app_env == DEVELOPMENT:
            return DEFAULT_DEVELOPMENT_CORS_ORIGINS

        return ()

    return tuple(
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    )


def _read_bool(name: str, *, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise RuntimeError(
        f"{name} must be a boolean value: true or false"
    )
