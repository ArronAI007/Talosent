"""Tool schema definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolSpec:
    name: str
    summary: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_openai_tool(self) -> dict[str, Any]:
        parameters = self.input_schema or {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.summary,
                "parameters": parameters,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ToolSpec":
        name = _require_text(data.get("name"), "ToolSpec.name")
        input_schema = data.get("input_schema") or {}
        output_schema = data.get("output_schema") or {}
        metadata = data.get("metadata") or {}
        if not isinstance(input_schema, Mapping):
            raise TypeError("ToolSpec.input_schema must be a mapping")
        if not isinstance(output_schema, Mapping):
            raise TypeError("ToolSpec.output_schema must be a mapping")
        if not isinstance(metadata, Mapping):
            raise TypeError("ToolSpec.metadata must be a mapping")
        return cls(
            name=name,
            summary=str(data.get("summary") or ""),
            input_schema=dict(input_schema),
            output_schema=dict(output_schema),
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
