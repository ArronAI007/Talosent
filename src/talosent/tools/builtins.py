"""Built-in tools available to every runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from talosent.tools.registry import ToolRegistry
from talosent.tools.spec import ToolSpec


def current_time_tool(arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}
    timezone_name = str(arguments.get("timezone") or "UTC").strip() or "UTC"
    tz = _resolve_timezone(timezone_name)
    now = datetime.now(tz)
    offset = now.utcoffset()

    return {
        "timezone": timezone_name,
        "iso": now.isoformat(),
        "unix": now.timestamp(),
        "offset_seconds": int(offset.total_seconds()) if offset is not None else 0,
    }


def current_time_spec() -> ToolSpec:
    return ToolSpec(
        name="current_time",
        summary="Return the current time in UTC or a requested IANA timezone.",
        input_schema={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "An IANA timezone name such as UTC or Asia/Shanghai.",
                }
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "timezone": {"type": "string"},
                "iso": {"type": "string"},
                "unix": {"type": "number"},
                "offset_seconds": {"type": "number"},
            },
        },
        metadata={
            "category": "time",
        },
    )


def register_builtin_tools(registry: ToolRegistry) -> ToolRegistry:
    registry.register(current_time_spec(), current_time_tool)
    return registry


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    return register_builtin_tools(registry)


def _resolve_timezone(timezone_name: str) -> timezone | ZoneInfo:
    if timezone_name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except Exception as exc:  # pragma: no cover - zoneinfo exception type varies
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc
