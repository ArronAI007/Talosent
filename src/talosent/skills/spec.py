"""Skill metadata definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SkillSpec:
    name: str
    summary: str = ""
    instructions: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "instructions": self.instructions,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SkillSpec":
        name = _require_text(data.get("name"), "SkillSpec.name")
        inputs = data.get("inputs") or ()
        outputs = data.get("outputs") or ()
        metadata = data.get("metadata") or {}
        if isinstance(inputs, Mapping) or isinstance(inputs, (str, bytes)):
            raise TypeError("SkillSpec.inputs must be an iterable of strings")
        if isinstance(outputs, Mapping) or isinstance(outputs, (str, bytes)):
            raise TypeError("SkillSpec.outputs must be an iterable of strings")
        if not isinstance(metadata, Mapping):
            raise TypeError("SkillSpec.metadata must be a mapping")
        return cls(
            name=name,
            summary=str(data.get("summary") or ""),
            instructions=str(data.get("instructions") or ""),
            inputs=tuple(str(item) for item in inputs),
            outputs=tuple(str(item) for item in outputs),
            metadata=dict(metadata),
        )

    def describe(self) -> str:
        if self.summary:
            return f"{self.name}: {self.summary}"
        return self.name


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text
