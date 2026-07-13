"""OpenAI-compatible chat completions provider."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from talosent.agent.model import AgentMessage, ToolCall
from talosent.providers.runtime import ProviderResponse
from talosent.tools.spec import ToolSpec


RequestFn = Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]


@dataclass(slots=True)
class OpenAICompatibleProvider:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 30.0
    name: str = "openai_compatible"
    request_fn: RequestFn | None = None

    def complete(
        self,
        messages: list[AgentMessage] | tuple[AgentMessage, ...] | Any,
        tools: list[ToolSpec] | tuple[ToolSpec, ...] | Any = (),
    ) -> ProviderResponse:
        if not self.api_key:
            raise RuntimeError("OpenAI-compatible provider requires an API key")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._serialize_message(message) for message in messages],
        }
        if tools:
            payload["tools"] = [tool.to_openai_tool() for tool in tools]
            payload["tool_choice"] = "auto"

        response = self._request_json(payload)
        return self._parse_response(response)

    def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = self._endpoint()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "talosent/0.1.0",
        }
        if self.request_fn is not None:
            return self.request_fn(endpoint, payload, headers, self.timeout)
        return self._post_json(endpoint, payload, headers, self.timeout)

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", "replace")
            raise RuntimeError(
                f"OpenAI-compatible request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc.reason}") from exc
        return json.loads(raw)

    def _endpoint(self) -> str:
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def _serialize_message(self, message: AgentMessage) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": message.role,
            "content": message.content or None,
        }
        if message.name:
            payload["name"] = message.name
        if message.tool_call_id:
            payload["tool_call_id"] = message.tool_call_id
        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments, ensure_ascii=False, sort_keys=True),
                    },
                }
                for tool_call in message.tool_calls
            ]
        return payload

    def _parse_response(self, payload: dict[str, Any]) -> ProviderResponse:
        choices = payload.get("choices") or []
        if not choices:
            return ProviderResponse(raw=payload, model=payload.get("model"))

        choice = choices[0]
        message = choice.get("message") or {}
        tool_calls = tuple(self._parse_tool_call(entry) for entry in message.get("tool_calls") or [])
        return ProviderResponse(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            model=payload.get("model"),
            finish_reason=choice.get("finish_reason"),
            raw=payload,
        )

    def _parse_tool_call(self, payload: dict[str, Any]) -> ToolCall:
        function = payload.get("function") or {}
        arguments_raw = function.get("arguments") or ""
        try:
            arguments = json.loads(arguments_raw) if arguments_raw else {}
        except json.JSONDecodeError:
            arguments = {"_raw": arguments_raw}
        return ToolCall(
            id=payload.get("id") or uuid4().hex,
            name=function.get("name") or "",
            arguments=arguments,
        )

