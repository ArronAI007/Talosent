"""Plugin metadata definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginSpec:
    name: str
    version: str = "0.1.0"
    summary: str = ""
    entrypoint: str = ""
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

