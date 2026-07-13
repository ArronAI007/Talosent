"""Offline heuristic provider for local development and demos."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from talosent.agent.model import AgentMessage, ToolCall
from talosent.providers.runtime import ProviderResponse
from talosent.tools.spec import ToolSpec


_TIME_HINT = re.compile(r"\b(time|clock|current time|timezone)\b", re.IGNORECASE)


@dataclass(slots=True)
class LocalHeuristicProvider:
    name: str = "local"

    def complete(
        self,
        messages: list[AgentMessage] | tuple[AgentMessage, ...] | Any,
        tools: list[ToolSpec] | tuple[ToolSpec, ...] | Any = (),
    ) -> ProviderResponse:
        last_message = self._last_message(messages)
        if last_message is not None and last_message.role == "tool":
            return self._respond_to_tool(last_message)

        last_user = self._last_message(messages, "user")
        if last_user is None:
            return ProviderResponse(content="Hello. Ask me something and I will help.")

        if self._should_call_time_tool(last_user.content, tools):
            return ProviderResponse(
                tool_calls=(
                    ToolCall(
                        id=uuid4().hex,
                        name="current_time",
                        arguments={"timezone": self._guess_timezone(last_user.content)},
                    ),
                ),
            )

        return ProviderResponse(content=f"You said: {last_user.content}")

    def _last_message(self, messages: Any, role: str | None = None) -> AgentMessage | None:
        for message in reversed(list(messages)):
            if role is None or message.role == role:
                return message
        return None

    def _should_call_time_tool(self, prompt: str, tools: Any) -> bool:
        has_time_tool = any(tool.name == "current_time" for tool in tools)
        return has_time_tool and bool(_TIME_HINT.search(prompt))

    def _guess_timezone(self, prompt: str) -> str:
        text = prompt.lower()
        if "shanghai" in text or "北京时间" in prompt:
            return "Asia/Shanghai"
        if "utc" in text or "gmt" in text:
            return "UTC"
        return "UTC"

    def _respond_to_tool(self, message: AgentMessage) -> ProviderResponse:
        if message.name != "current_time":
            return ProviderResponse(content=f"Tool {message.name or 'unknown'} returned {message.content}")

        try:
            payload = json.loads(message.content)
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict) and payload.get("iso"):
            timezone_name = payload.get("timezone", "UTC")
            return ProviderResponse(
                content=f"The current time in {timezone_name} is {payload['iso']}.",
            )

        return ProviderResponse(content=f"The current time tool returned: {message.content}")
