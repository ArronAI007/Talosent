from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentContext, ToolCall
from talosent.agent.workflows import ChatWorkflow, WorkflowSpec
from talosent.providers import ProviderResponse
from talosent.storage import InMemoryStorageBackend
from talosent.memory import PersistentMemoryStore
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

    def test_chat_workflow_persists_and_restores_session(self) -> None:
        snapshots: list[list[str]] = []
        store = PersistentMemoryStore(InMemoryStorageBackend(), namespace="sessions")

        class MemoryAwareProvider:
            name = "memory-aware"

            def complete(self, messages, tools=()):
                snapshot = [f"{message.role}:{message.content}" for message in messages]
                snapshots.append(snapshot)
                previous_assistant = next((message.content for message in messages if message.role == "assistant"), None)
                if previous_assistant is None:
                    return ProviderResponse(content="first-turn")
                return ProviderResponse(content=f"restored:{previous_assistant}")

        workflow = ChatWorkflow(
            spec=WorkflowSpec(name="chat-test"),
            provider=MemoryAwareProvider(),
            tools=build_tool_registry(),
            memory_store=store,
        )

        first = AgentContext(conversation_id="persist-1")
        first.add_message("user", "hello")
        first_result = workflow.run(first)
        self.assertEqual(first_result.state["final_message"], "first-turn")
        self.assertIsNotNone(store.get(workflow.session_key("persist-1")))

        second = AgentContext(conversation_id="persist-1")
        second.add_message("user", "hello again")
        second_result = workflow.run(second)

        self.assertTrue(second_result.state["session"]["loaded"])
        self.assertIn("restored:first-turn", second_result.state["final_message"])
        self.assertGreaterEqual(len(snapshots), 2)
        self.assertTrue(any(entry == "assistant:first-turn" for entry in snapshots[1]))
        self.assertTrue(any(message.role == "assistant" and message.content == "first-turn" for message in second.messages))

    def test_chat_workflow_compresses_old_history_before_provider_call(self) -> None:
        snapshots: list[list[dict[str, object]]] = []
        store = PersistentMemoryStore(InMemoryStorageBackend(), namespace="sessions")

        class InspectingProvider:
            name = "inspect"

            def complete(self, messages, tools=()):
                snapshots.append([message.to_dict() for message in messages])
                return ProviderResponse(content="compressed")

        workflow = ChatWorkflow(
            spec=WorkflowSpec(name="chat-test"),
            provider=InspectingProvider(),
            tools=build_tool_registry(),
            memory_store=store,
            compression_max_messages=4,
            compression_keep_messages=2,
            compression_summary_items=4,
            compression_summary_chars=600,
        )

        context = AgentContext(conversation_id="compress-1")
        context.add_message("user", "old question 1")
        context.add_message("assistant", "old answer 1")
        context.add_message("user", "old question 2")
        context.add_message("assistant", "old answer 2")
        context.add_message("user", "latest question")

        result = workflow.run(context)

        self.assertEqual(result.state["final_message"], "compressed")
        self.assertTrue(result.state["compression"]["applied"])
        self.assertTrue(any(message["metadata"].get("compressed_context") for message in snapshots[0] if message["role"] == "system"))
        self.assertTrue(any(message["content"] == "latest question" for message in snapshots[0] if message["role"] == "user"))

        stored = store.get(workflow.session_key("compress-1"))
        self.assertIsNotNone(stored)
        self.assertLess(len(stored.value["messages"]), 7)
        self.assertTrue(any(message["metadata"].get("compressed_context") for message in stored.value["messages"] if message["role"] == "system"))
