"""Storage backend abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(slots=True)
class StorageObject:
    key: str
    data: bytes
    content_type: str = "application/octet-stream"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StorageBackend(Protocol):
    def put(self, object_: StorageObject) -> None:
        """Persist an object."""

    def get(self, key: str) -> StorageObject | None:
        """Return an object if it exists."""

    def delete(self, key: str) -> None:
        """Remove an object if it exists."""

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """List all stored keys."""


class InMemoryStorageBackend:
    def __init__(self) -> None:
        self._objects: dict[str, StorageObject] = {}

    def put(self, object_: StorageObject) -> None:
        self._objects[object_.key] = object_

    def get(self, key: str) -> StorageObject | None:
        return self._objects.get(key)

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(key for key in self._objects if key.startswith(prefix))

    def clear(self) -> None:
        self._objects.clear()
