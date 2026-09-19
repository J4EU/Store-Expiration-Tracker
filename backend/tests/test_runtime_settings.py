from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi import Response

from app.auth import get_settings, set_session_cookie
from app.settings import get_runtime_settings


class RuntimeSettingsTest(unittest.TestCase):
    def tearDown(self) -> None:
        get_runtime_settings.cache_clear()
        get_settings.cache_clear()

    def test_defaults_to_development_runtime_settings(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = get_runtime_settings()

        self.assertEqual(settings.app_env, "development")
        self.assertFalse(settings.session_cookie_secure)
        self.assertTrue(settings.api_docs_enabled)
        self.assertIn("http://localhost:5173", settings.cors_allow_origins)

    def test_production_defaults_disable_dev_exposure(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            settings = get_runtime_settings()

        self.assertEqual(settings.app_env, "production")
        self.assertTrue(settings.session_cookie_secure)
        self.assertFalse(settings.api_docs_enabled)
        self.assertEqual(settings.cors_allow_origins, ())

    def test_explicit_runtime_values_override_defaults(self) -> None:
        env = {
            "APP_ENV": "development",
            "SESSION_COOKIE_SECURE": "true",
            "API_DOCS_ENABLED": "false",
            "CORS_ALLOW_ORIGINS": "http://example.local, http://admin.local",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_runtime_settings()

        self.assertTrue(settings.session_cookie_secure)
        self.assertFalse(settings.api_docs_enabled)
        self.assertEqual(
            settings.cors_allow_origins,
            ("http://example.local", "http://admin.local"),
        )

    def test_session_cookie_uses_runtime_secure_setting(self) -> None:
        env = {
            "APP_ENV": "production",
            "ADMIN_PASSWORD": "test-password",
            "SESSION_SECRET": "test-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            response = Response()
            set_session_cookie(response, get_settings(), "admin")

        self.assertIn("Secure", response.headers["set-cookie"])


if __name__ == "__main__":
    unittest.main()
