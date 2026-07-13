"""Provider composition helpers."""

from __future__ import annotations

import logging

from talosent.config import Settings
from talosent.providers.local import LocalHeuristicProvider
from talosent.providers.openai_compatible import OpenAICompatibleProvider
from talosent.providers.profile import ProviderProfile
from talosent.providers.registry import ProviderRegistry
from talosent.providers.runtime import ChatProvider

LOGGER = logging.getLogger(__name__)

_ALIASES = {
    "openai": "openai_compatible",
    "openai-compatible": "openai_compatible",
}


def build_provider_registry(settings: Settings) -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(
        ProviderProfile(
            name="local",
            family="local",
            model=settings.default_model,
            description="Heuristic fallback provider for offline demos.",
        ),
        lambda profile: LocalHeuristicProvider(name=profile.name),
    )

    if settings.openai_api_key:
        registry.register(
            ProviderProfile(
                name="openai_compatible",
                family="openai-compatible",
                model=settings.default_model,
                description="OpenAI-compatible chat completions provider.",
                api_base=settings.openai_base_url,
                api_key_env="TALOSENT_OPENAI_API_KEY",
            ),
            lambda profile: OpenAICompatibleProvider(
                api_key=settings.openai_api_key or "",
                model=profile.model,
                base_url=profile.api_base or settings.openai_base_url,
                name=profile.name,
            ),
        )

    return registry


def build_provider(settings: Settings) -> ChatProvider:
    registry = build_provider_registry(settings)
    preferred = _ALIASES.get(settings.default_provider, settings.default_provider)

    if preferred in registry:
        return registry.create(preferred)

    if preferred != "local":
        LOGGER.warning(
            "Provider %r is unavailable; falling back to the local heuristic provider.",
            settings.default_provider,
        )
    return registry.create("local")
