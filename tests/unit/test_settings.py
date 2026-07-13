from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.config import load_settings


class SettingsTests(unittest.TestCase):
    def test_load_settings_uses_environment_overrides(self) -> None:
        settings = load_settings(
            {
                "TALOSENT_APP_NAME": "Demo Agent",
                "TALOSENT_ENV": "production",
                "TALOSENT_LOG_LEVEL": "debug",
                "TALOSENT_PROVIDER": "openai",
                "TALOSENT_MODEL": "gpt-5",
                "TALOSENT_OPENAI_API_KEY": "secret-key",
                "TALOSENT_OPENAI_BASE_URL": "https://example.com/v1",
                "TALOSENT_MEMORY_BACKEND": "sqlite",
                "TALOSENT_STORAGE_BACKEND": "filesystem",
                "TALOSENT_API_HOST": "0.0.0.0",
                "TALOSENT_API_PORT": "9000",
                "TALOSENT_WEB_ENABLED": "true",
                "TALOSENT_TUI_ENABLED": "on",
            }
        )

        self.assertEqual(settings.app_name, "Demo Agent")
        self.assertEqual(settings.environment, "production")
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.default_provider, "openai")
        self.assertEqual(settings.default_model, "gpt-5")
        self.assertEqual(settings.openai_api_key, "secret-key")
        self.assertEqual(settings.openai_base_url, "https://example.com/v1")
        self.assertEqual(settings.memory_backend, "sqlite")
        self.assertEqual(settings.storage_backend, "filesystem")
        self.assertEqual(settings.api_host, "0.0.0.0")
        self.assertEqual(settings.api_port, 9000)
        self.assertTrue(settings.web_enabled)
        self.assertTrue(settings.tui_enabled)

    def test_settings_to_dict_round_trips(self) -> None:
        settings = load_settings()
        data = settings.to_dict()

        self.assertEqual(data["app_name"], "Talosent")
        self.assertEqual(data["api_port"], 8000)
