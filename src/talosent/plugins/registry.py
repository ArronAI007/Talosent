"""Plugin registry."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from talosent.plugins.spec import PluginSpec


@dataclass(slots=True)
class PluginRegistration:
    spec: PluginSpec


class PluginRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, PluginRegistration] = {}

    def register(self, spec: PluginSpec) -> PluginRegistration:
        registration = PluginRegistration(spec=spec)
        self._registrations[spec.name] = registration
        return registration

    def register_many(self, specs: Iterable[PluginSpec]) -> tuple[PluginRegistration, ...]:
        stored: list[PluginRegistration] = []
        for spec in specs:
            stored.append(self.register(spec))
        return tuple(stored)

    def get(self, name: str) -> PluginRegistration:
        return self._registrations[name]

    def items(self) -> tuple[PluginRegistration, ...]:
        return tuple(self._registrations.values())

    def specs(self) -> tuple[PluginSpec, ...]:
        return tuple(registration.spec for registration in self._registrations.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._registrations)

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return {name: registration.spec.to_dict() for name, registration in self._registrations.items()}

    def describe(self, name: str) -> str:
        return self.get(name).spec.describe()

    def __contains__(self, name: object) -> bool:
        return name in self._registrations
