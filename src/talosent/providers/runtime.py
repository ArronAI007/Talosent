"""Shared provider runtime contracts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from talosent.agent.model import AgentMessage, ToolCall
from talosent.tools.spec import ToolSpec


@dataclass(slots=True)
class ProviderResponse:
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    model: str | None = None
    finish_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class ChatProvider(Protocol):
    name: str

    def complete(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec] = (),
    ) -> ProviderResponse:
        """Return the next provider response for the given conversation."""

