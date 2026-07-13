"""Skill metadata definitions."""

from __future__ import annotations

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

