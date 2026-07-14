"""Memory storage abstractions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Iterable, Mapping
from typing import Any, Protocol

from talosent.storage.backend import StorageBackend, StorageObject, build_storage_backend


@dataclass(slots=True)
class MemoryEntry:
    key: str
    value: Any
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryEntry":
        key = _require_text(data.get("key"), "MemoryEntry.key")
        tags_raw = data.get("tags") or ()
        if isinstance(tags_raw, Mapping) or isinstance(tags_raw, (str, bytes)):
            raise TypeError("MemoryEntry.tags must be an iterable of strings")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("MemoryEntry.metadata must be a mapping")
        return cls(
            key=key,
            value=data.get("value"),
            tags=tuple(str(tag) for tag in tags_raw),
            metadata=dict(metadata),
            created_at=_parse_datetime(data.get("created_at")),
        )

    def to_storage_object(self, storage_key: str) -> StorageObject:
        return StorageObject(
            key=storage_key,
            data=json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ).encode("utf-8"),
            content_type="application/json",
            metadata={"kind": "memory_entry"},
            created_at=self.created_at,
        )

    @classmethod
    def from_storage_object(cls, object_: StorageObject) -> "MemoryEntry":
        payload = json.loads(object_.data.decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("Stored memory payload must be a JSON object")
        return cls.from_dict(payload)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


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
        return tuple(sorted(self._entries.values(), key=lambda entry: (entry.created_at, entry.key)))

    def clear(self) -> None:
        self._entries.clear()

    def upsert_many(self, entries: Iterable[MemoryEntry]) -> tuple[MemoryEntry, ...]:
        stored: list[MemoryEntry] = []
        for entry in entries:
            self.put(entry)
            stored.append(entry)
        return tuple(stored)

    def find_by_tag(self, tag: str) -> tuple[MemoryEntry, ...]:
        return tuple(entry for entry in self.items() if entry.has_tag(tag))

    def __len__(self) -> int:
        return len(self._entries)


class PersistentMemoryStore:
    """Persist memory entries through a storage backend."""

    def __init__(
        self,
        backend: StorageBackend | None = None,
        *,
        namespace: str = "memory",
    ) -> None:
        self.backend = backend or build_storage_backend("filesystem")
        self.namespace = _normalize_namespace(namespace)

    def put(self, entry: MemoryEntry) -> None:
        self.backend.put(entry.to_storage_object(self._storage_key(entry.key)))

    def get(self, key: str) -> MemoryEntry | None:
        object_ = self.backend.get(self._storage_key(key))
        if object_ is None:
            return None
        return MemoryEntry.from_storage_object(object_)

    def delete(self, key: str) -> None:
        self.backend.delete(self._storage_key(key))

    def items(self) -> tuple[MemoryEntry, ...]:
        entries = []
        for storage_key in self.backend.keys(prefix=self._prefix()):
            entry = self.get(self._strip_prefix(storage_key))
            if entry is not None:
                entries.append(entry)
        return tuple(sorted(entries, key=lambda item: (item.created_at, item.key)))

    def clear(self) -> None:
        for storage_key in self.backend.keys(prefix=self._prefix()):
            self.backend.delete(storage_key)

    def upsert_many(self, entries: Iterable[MemoryEntry]) -> tuple[MemoryEntry, ...]:
        stored: list[MemoryEntry] = []
        for entry in entries:
            self.put(entry)
            stored.append(entry)
        return tuple(stored)

    def find_by_tag(self, tag: str) -> tuple[MemoryEntry, ...]:
        return tuple(entry for entry in self.items() if entry.has_tag(tag))

    def __len__(self) -> int:
        return len(self.items())

    def _storage_key(self, key: str) -> str:
        return f"{self.namespace}/{_require_text(key, 'MemoryEntry.key')}"

    def _strip_prefix(self, storage_key: str) -> str:
        prefix = self._prefix()
        if storage_key.startswith(prefix):
            return storage_key[len(prefix) :]
        return storage_key

    def _prefix(self) -> str:
        return f"{self.namespace}/"


def build_memory_store(
    kind: str = "in_memory",
    *,
    storage_backend: StorageBackend | None = None,
    namespace: str = "memory",
) -> MemoryStore:
    normalized = kind.replace("-", "_").strip().lower()
    if normalized in {"in_memory", "memory", "mem"}:
        return InMemoryMemoryStore()
    if normalized in {"filesystem", "file_system", "persistent", "storage"}:
        return PersistentMemoryStore(storage_backend=storage_backend, namespace=namespace)
    raise ValueError(f"Unknown memory backend: {kind}")


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_namespace(namespace: str) -> str:
    text = str(namespace or "").strip().strip("/")
    return text or "memory"
