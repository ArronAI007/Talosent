"""Storage backend abstractions."""

from __future__ import annotations

import base64
import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class StorageObject:
    key: str
    data: bytes
    content_type: str = "application/octet-stream"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "data": base64.b64encode(self.data).decode("ascii"),
            "encoding": "base64",
            "content_type": self.content_type,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StorageObject":
        key = _require_text(data.get("key"), "StorageObject.key")
        raw_data = data.get("data")
        encoding = str(data.get("encoding") or "base64").lower()
        if isinstance(raw_data, bytes):
            payload = raw_data
        elif raw_data is None:
            payload = b""
        elif encoding == "base64":
            payload = base64.b64decode(str(raw_data).encode("ascii"))
        elif encoding in {"text", "utf-8", "utf8"}:
            payload = str(raw_data).encode("utf-8")
        else:
            raise ValueError(f"Unsupported storage encoding: {encoding}")

        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("StorageObject.metadata must be a mapping")

        return cls(
            key=key,
            data=payload,
            content_type=str(data.get("content_type") or "application/octet-stream"),
            metadata=dict(metadata),
            created_at=_parse_datetime(data.get("created_at")),
        )

    def copy(self, **overrides: Any) -> "StorageObject":
        payload = self.to_dict()
        payload.update(overrides)
        return StorageObject.from_dict(payload)


class StorageBackend(Protocol):
    def put(self, object_: StorageObject) -> None:
        """Persist an object."""

    def get(self, key: str) -> StorageObject | None:
        """Return an object if it exists."""

    def delete(self, key: str) -> None:
        """Remove an object if it exists."""

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """List all stored keys."""

    def items(self) -> tuple[StorageObject, ...]:
        """List all stored objects."""

    def clear(self) -> None:
        """Remove all stored objects."""


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
        return tuple(sorted(key for key in self._objects if key.startswith(prefix)))

    def items(self) -> tuple[StorageObject, ...]:
        return tuple(sorted(self._objects.values(), key=lambda item: (item.created_at, item.key)))

    def clear(self) -> None:
        self._objects.clear()


class FilesystemStorageBackend:
    """Persist storage objects as JSON envelopes on disk."""

    def __init__(self, root_path: str | Path | None = None) -> None:
        self.root_path = Path(root_path or tempfile.mkdtemp(prefix="talosent-storage-"))
        self.root_path.mkdir(parents=True, exist_ok=True)

    def put(self, object_: StorageObject) -> None:
        path = self._path_for_key(object_.key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(object_.to_dict(), ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

    def get(self, key: str) -> StorageObject | None:
        path = self._path_for_key(key)
        if not path.exists():
            return None
        return StorageObject.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, key: str) -> None:
        path = self._path_for_key(key)
        path.unlink(missing_ok=True)

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(
            object_.key
            for object_ in self.items()
            if object_.key.startswith(prefix)
        )

    def items(self) -> tuple[StorageObject, ...]:
        objects = [StorageObject.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in self._iter_paths()]
        return tuple(sorted(objects, key=lambda item: (item.created_at, item.key)))

    def clear(self) -> None:
        for path in self._iter_paths():
            path.unlink(missing_ok=True)

    def _iter_paths(self) -> tuple[Path, ...]:
        if not self.root_path.exists():
            return ()
        return tuple(sorted(path for path in self.root_path.rglob("*.json") if path.is_file()))

    def _path_for_key(self, key: str) -> Path:
        normalized_key = _require_text(key, "StorageObject.key")
        digest = hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()
        return self.root_path / digest[:2] / f"{digest[2:]}.json"


def build_storage_backend(
    kind: str = "in_memory",
    *,
    root_path: str | Path | None = None,
) -> StorageBackend:
    normalized = kind.replace("-", "_").strip().lower()
    if normalized in {"in_memory", "memory", "mem"}:
        return InMemoryStorageBackend()
    if normalized in {"filesystem", "file_system", "fs", "persistent"}:
        return FilesystemStorageBackend(root_path=root_path)
    raise ValueError(f"Unknown storage backend: {kind}")


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
