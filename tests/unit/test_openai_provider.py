from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentMessage, ToolCall
from talosent.providers import OpenAICompatibleProvider
from talosent.tools import ToolSpec


class OpenAICompatibleProviderTests(unittest.TestCase):
    def test_complete_serializes_messages_and_parses_tool_calls(self) -> None:
        captured: dict[str, object] = {}

        def fake_request(
            url: str,
            payload: dict[str, object],
            headers: dict[str, str],
            timeout: float,
        ) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {
                "model": "demo-model",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "The tool is ready.",
                            "tool_calls": [
                                {
                                    "id": "call-2",
                                    "type": "function",
                                    "function": {
                                        "name": "current_time",
                                        "arguments": "{\"timezone\":\"UTC\"}",
                                    },
                                }
                            ],
                        },
                    }
                ],
            }

        provider = OpenAICompatibleProvider(
            api_key="secret-key",
            model="demo-model",
            base_url="https://example.com/v1",
            request_fn=fake_request,
        )

        response = provider.complete(
            [
                AgentMessage(role="system", content="You are helpful."),
                AgentMessage(role="user", content="what time is it?"),
                AgentMessage(
                    role="assistant",
                    content="",
                    tool_calls=(
                        ToolCall(
                            id="call-1",
                            name="current_time",
                            arguments={"timezone": "UTC"},
                        ),
                    ),
                ),
                AgentMessage(
                    role="tool",
                    content='{"timezone":"UTC","iso":"2026-07-13T00:00:00+00:00"}',
                    name="current_time",
                    tool_call_id="call-1",
                ),
            ],
            tools=[
                ToolSpec(
                    name="current_time",
                    summary="Return the current time.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "timezone": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                )
            ],
        )

        self.assertEqual(captured["url"], "https://example.com/v1/chat/completions")
        self.assertEqual(captured["timeout"], 30.0)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret-key")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["model"], "demo-model")
        self.assertEqual(payload["tools"][0]["function"]["name"], "current_time")
        self.assertEqual(payload["messages"][2]["tool_calls"][0]["function"]["name"], "current_time")
        self.assertEqual(payload["messages"][3]["tool_call_id"], "call-1")

        self.assertEqual(response.content, "The tool is ready.")
        self.assertEqual(len(response.tool_calls), 1)
        self.assertEqual(response.tool_calls[0].name, "current_time")
        self.assertEqual(response.tool_calls[0].arguments, {"timezone": "UTC"})
