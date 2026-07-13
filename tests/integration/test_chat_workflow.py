from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentContext, ToolCall
from talosent.agent.workflows import ChatWorkflow, WorkflowSpec
from talosent.providers import ProviderResponse
from talosent.tools import build_tool_registry


class ChatWorkflowIntegrationTests(unittest.TestCase):
    def test_chat_workflow_runs_tool_loop(self) -> None:
        outer = self

        class ScriptedProvider:
            name = "scripted"

            def __init__(self) -> None:
                self.calls = 0

            def complete(self, messages, tools=()):
                self.calls += 1
                if self.calls == 1:
                    outer.assertTrue(any(tool.name == "current_time" for tool in tools))
                    return ProviderResponse(
                        tool_calls=(
                            ToolCall(
                                id="call-1",
                                name="current_time",
                                arguments={"timezone": "UTC"},
                            ),
                        )
                    )

                last_tool = next(message for message in reversed(messages) if message.role == "tool")
                return ProviderResponse(content=f"Tool said: {last_tool.content}")

        provider = ScriptedProvider()
        workflow = ChatWorkflow(
            spec=WorkflowSpec(name="chat-test"),
            provider=provider,
            tools=build_tool_registry(),
            max_turns=4,
        )
        context = AgentContext()
        context.add_message("user", "what time is it?")

        result = workflow.run(context)

        self.assertEqual(result.state["provider"], "scripted")
        self.assertEqual(result.state["turns"], 2)
        self.assertIn("Tool said:", result.state["final_message"])
        self.assertTrue(any(message.role == "tool" and message.name == "current_time" for message in context.messages))
        self.assertTrue(any(message.role == "assistant" and message.content.startswith("Tool said:") for message in context.messages))
