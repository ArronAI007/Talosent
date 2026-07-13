"""Provider registry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from talosent.providers.profile import ProviderProfile


ProviderFactory = Callable[[ProviderProfile], Any]


@dataclass(slots=True)
class ProviderRegistration:
    profile: ProviderProfile
    factory: ProviderFactory | None = None


class ProviderRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, ProviderRegistration] = {}

    def register(
        self,
        profile: ProviderProfile,
        factory: ProviderFactory | None = None,
    ) -> ProviderRegistration:
        registration = ProviderRegistration(profile=profile, factory=factory)
        self._registrations[profile.name] = registration
        return registration

    def get(self, name: str) -> ProviderRegistration:
        return self._registrations[name]

    def resolve(self, name: str) -> ProviderProfile:
        return self.get(name).profile

    def create(self, name: str) -> Any:
        registration = self.get(name)
        if registration.factory is None:
            raise KeyError(f"provider '{name}' does not have a factory")
        return registration.factory(registration.profile)

    def items(self) -> tuple[ProviderRegistration, ...]:
        return tuple(self._registrations.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._registrations)

    def __contains__(self, name: object) -> bool:
        return name in self._registrations

