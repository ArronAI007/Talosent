"""Gateway contracts and registry."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class GatewayRequest:
    channel: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GatewayRequest":
        channel = _require_text(data.get("channel"), "GatewayRequest.channel")
        payload = data.get("payload") or {}
        metadata = data.get("metadata") or {}
        if not isinstance(payload, Mapping):
            raise TypeError("GatewayRequest.payload must be a mapping")
        if not isinstance(metadata, Mapping):
            raise TypeError("GatewayRequest.metadata must be a mapping")
        return cls(channel=channel, payload=dict(payload), metadata=dict(metadata))


@dataclass(slots=True)
class GatewayResponse:
    ok: bool = True
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "payload": dict(self.payload),
            "error": self.error,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GatewayResponse":
        payload = data.get("payload") or {}
        metadata = data.get("metadata") or {}
        if not isinstance(payload, Mapping):
            raise TypeError("GatewayResponse.payload must be a mapping")
        if not isinstance(metadata, Mapping):
            raise TypeError("GatewayResponse.metadata must be a mapping")
        return cls(
            ok=bool(data.get("ok", True)),
            payload=dict(payload),
            error=_optional_text(data.get("error")),
            metadata=dict(metadata),
        )


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

    def register_many(self, adapters: Iterable[GatewayAdapter]) -> tuple[GatewayAdapter, ...]:
        stored: list[GatewayAdapter] = []
        for adapter in adapters:
            stored.append(self.register(adapter))
        return tuple(stored)

    def get(self, name: str) -> GatewayAdapter:
        return self._adapters[name].adapter

    def dispatch(self, request: GatewayRequest) -> GatewayResponse:
        return self.get(request.channel).send(request)

    def dispatch_many(self, requests: Iterable[GatewayRequest]) -> tuple[GatewayResponse, ...]:
        return tuple(self.dispatch(request) for request in requests)

    def items(self) -> tuple[GatewayAdapter, ...]:
        return tuple(item.adapter for item in self._adapters.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._adapters)

    def has(self, name: str) -> bool:
        return name in self._adapters

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "name": item.adapter.name,
                "adapter": item.adapter.__class__.__name__,
            }
            for name, item in self._adapters.items()
        }

    def describe(self, name: str) -> str:
        return self.get(name).__class__.__name__

    def __contains__(self, name: object) -> bool:
        return name in self._adapters


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
