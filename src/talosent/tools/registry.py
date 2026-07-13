"""Tool registry and invocation helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from talosent.tools.spec import ToolSpec


ToolHandler = Callable[[Mapping[str, Any]], Any]


@dataclass(slots=True)
class ToolRegistration:
    spec: ToolSpec
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, ToolRegistration] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> ToolRegistration:
        registration = ToolRegistration(spec=spec, handler=handler)
        self._registrations[spec.name] = registration
        return registration

    def get(self, name: str) -> ToolRegistration:
        return self._registrations[name]

    def invoke(self, name: str, arguments: Mapping[str, Any] | None = None) -> Any:
        registration = self.get(name)
        return registration.handler(arguments or {})

    def items(self) -> tuple[ToolRegistration, ...]:
        return tuple(self._registrations.values())

    def specs(self) -> tuple[ToolSpec, ...]:
        return tuple(registration.spec for registration in self._registrations.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._registrations)

    def __contains__(self, name: object) -> bool:
        return name in self._registrations
