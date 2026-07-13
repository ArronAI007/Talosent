"""Memory storage abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(slots=True)
class MemoryEntry:
    key: str
    value: Any
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryStore(Protocol):
    def put(self, entry: MemoryEntry) -> None:
        """Persist an entry."""

    def get(self, key: str) -> MemoryEntry | None:
        """Return a stored entry if it exists."""

    def delete(self, key: str) -> None:
        """Remove an entry if it exists."""

    def items(self) -> tuple[MemoryEntry, ...]:
        """List all entries."""


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}

    def put(self, entry: MemoryEntry) -> None:
        self._entries[entry.key] = entry

    def get(self, key: str) -> MemoryEntry | None:
        return self._entries.get(key)

    def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    def items(self) -> tuple[MemoryEntry, ...]:
        return tuple(self._entries.values())

    def clear(self) -> None:
        self._entries.clear()
