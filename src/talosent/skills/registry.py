"""Skill registry."""

from __future__ import annotations

from dataclasses import dataclass

from talosent.skills.spec import SkillSpec


@dataclass(slots=True)
class SkillRegistration:
    spec: SkillSpec


class SkillRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, SkillRegistration] = {}

    def register(self, spec: SkillSpec) -> SkillRegistration:
        registration = SkillRegistration(spec=spec)
        self._registrations[spec.name] = registration
        return registration

    def get(self, name: str) -> SkillRegistration:
        return self._registrations[name]

    def items(self) -> tuple[SkillRegistration, ...]:
        return tuple(self._registrations.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._registrations)

    def __contains__(self, name: object) -> bool:
        return name in self._registrations

