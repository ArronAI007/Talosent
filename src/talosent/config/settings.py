"""Environment-backed settings for Talosent."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | int | None, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    text = value.strip()
    if not text:
        return default
    return int(text)


@dataclass(slots=True)
class Settings:
    app_name: str = "Talosent"
    environment: str = "development"
    log_level: str = "INFO"
    default_provider: str = "local"
    default_model: str = "stub"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    memory_backend: str = "in_memory"
    storage_backend: str = "filesystem"
    recent_turns: int = 4
    memory_fact_limit: int = 8
    summary_turn_preview_limit: int = 8
    summary_char_limit: int = 2000
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    web_enabled: bool = False
    tui_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ

    return Settings(
        app_name=env.get("TALOSENT_APP_NAME", "Talosent"),
        environment=env.get("TALOSENT_ENV", "development"),
        log_level=env.get("TALOSENT_LOG_LEVEL", "INFO").upper(),
        default_provider=env.get("TALOSENT_PROVIDER", "local"),
        default_model=env.get("TALOSENT_MODEL", "stub"),
        openai_api_key=env.get("TALOSENT_OPENAI_API_KEY") or None,
        openai_base_url=env.get("TALOSENT_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        memory_backend=env.get("TALOSENT_MEMORY_BACKEND", "in_memory"),
        storage_backend=env.get("TALOSENT_STORAGE_BACKEND", "filesystem"),
        recent_turns=_parse_int(env.get("TALOSENT_RECENT_TURNS"), 4),
        memory_fact_limit=_parse_int(env.get("TALOSENT_MEMORY_FACT_LIMIT"), 8),
        summary_turn_preview_limit=_parse_int(
            env.get("TALOSENT_SUMMARY_TURN_PREVIEW_LIMIT"),
            8,
        ),
        summary_char_limit=_parse_int(env.get("TALOSENT_SUMMARY_CHAR_LIMIT"), 2000),
        api_host=env.get("TALOSENT_API_HOST", "127.0.0.1"),
        api_port=_parse_int(env.get("TALOSENT_API_PORT"), 8000),
        web_enabled=_parse_bool(env.get("TALOSENT_WEB_ENABLED")),
        tui_enabled=_parse_bool(env.get("TALOSENT_TUI_ENABLED")),
    )
