"""Provider profile definitions."""

from __future__ import annotations

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

