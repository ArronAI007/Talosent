"""Plugin metadata definitions."""

from __future__ import annotations

from collections.abc import Mapping
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "summary": self.summary,
            "entrypoint": self.entrypoint,
            "skills": list(self.skills),
            "tools": list(self.tools),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PluginSpec":
        name = _require_text(data.get("name"), "PluginSpec.name")
        skills = data.get("skills") or ()
        tools = data.get("tools") or ()
        metadata = data.get("metadata") or {}
        if isinstance(skills, Mapping) or isinstance(skills, (str, bytes)):
            raise TypeError("PluginSpec.skills must be an iterable of strings")
        if isinstance(tools, Mapping) or isinstance(tools, (str, bytes)):
            raise TypeError("PluginSpec.tools must be an iterable of strings")
        if not isinstance(metadata, Mapping):
            raise TypeError("PluginSpec.metadata must be a mapping")
        return cls(
            name=name,
            version=str(data.get("version") or "0.1.0"),
            summary=str(data.get("summary") or ""),
            entrypoint=str(data.get("entrypoint") or ""),
            skills=tuple(str(item) for item in skills),
            tools=tuple(str(item) for item in tools),
            metadata=dict(metadata),
        )

    def describe(self) -> str:
        if self.summary:
            return f"{self.name} {self.version}: {self.summary}"
        return f"{self.name} {self.version}"


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text
