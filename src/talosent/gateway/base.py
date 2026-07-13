"""Gateway contracts and registry."""

from __future__ import annotations

from typing import Any, Protocol
from dataclasses import dataclass, field


@dataclass(slots=True)
class GatewayRequest:
    channel: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GatewayResponse:
    ok: bool = True
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class GatewayAdapter(Protocol):
    name: str

    def send(self, request: GatewayRequest) -> GatewayResponse:
        """Send a request through the gateway."""


@dataclass(slots=True)
class _RegisteredGateway:
    adapter: GatewayAdapter


class GatewayRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, _RegisteredGateway] = {}

    def register(self, adapter: GatewayAdapter) -> GatewayAdapter:
        self._adapters[adapter.name] = _RegisteredGateway(adapter=adapter)
        return adapter

    def get(self, name: str) -> GatewayAdapter:
        return self._adapters[name].adapter

    def dispatch(self, request: GatewayRequest) -> GatewayResponse:
        return self.get(request.channel).send(request)

    def items(self) -> tuple[GatewayAdapter, ...]:
        return tuple(item.adapter for item in self._adapters.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._adapters)

    def __contains__(self, name: object) -> bool:
        return name in self._adapters
