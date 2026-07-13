"""Plugin registry."""

from __future__ import annotations

from dataclasses import dataclass

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

    def get(self, name: str) -> PluginRegistration:
        return self._registrations[name]

    def items(self) -> tuple[PluginRegistration, ...]:
        return tuple(self._registrations.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._registrations)

    def __contains__(self, name: object) -> bool:
        return name in self._registrations

