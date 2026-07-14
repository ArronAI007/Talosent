"""Provider profile definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderProfile:
    name: str
    family: str = "local"
    model: str = "stub"
    description: str = ""
    api_base: str | None = None
    api_key_env: str | None = None
    supports_streaming: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "model": self.model,
            "description": self.description,
            "api_base": self.api_base,
            "api_key_env": self.api_key_env,
            "supports_streaming": self.supports_streaming,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProviderProfile":
        name = _require_text(data.get("name"), "ProviderProfile.name")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("ProviderProfile.metadata must be a mapping")
        return cls(
            name=name,
            family=str(data.get("family") or "local"),
            model=str(data.get("model") or "stub"),
            description=str(data.get("description") or ""),
            api_base=_optional_text(data.get("api_base")),
            api_key_env=_optional_text(data.get("api_key_env")),
            supports_streaming=_parse_bool(data.get("supports_streaming")),
            metadata=dict(metadata),
        )

    @property
    def label(self) -> str:
        if self.description:
            return self.description
        return f"{self.family}:{self.model}"


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
