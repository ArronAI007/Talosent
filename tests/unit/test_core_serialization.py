from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentContext, AgentMessage, Artifact, ToolCall, WorkflowResult
from talosent.memory import InMemoryMemoryStore, MemoryEntry, PersistentMemoryStore
from talosent.plugins import PluginSpec
from talosent.providers import ProviderProfile
from talosent.skills import SkillSpec
from talosent.storage import FilesystemStorageBackend, StorageObject
from talosent.tools import ToolSpec


class CoreSerializationTests(unittest.TestCase):
    def test_agent_context_and_workflow_result_round_trip(self) -> None:
        context = AgentContext(conversation_id="conv-1")
        context.add_message("user", "hello", source="test")
        context.add_message(
            "assistant",
            "",
            tool_calls=(ToolCall(id="call-1", name="echo", arguments={"text": "hello"}),),
        )
        context.add_artifact("summary.txt", {"summary": "done"}, mime_type="application/json")

        restored = AgentContext.from_dict(context.to_dict())

        self.assertEqual(restored.conversation_id, "conv-1")
        self.assertEqual(restored.messages[0].metadata["source"], "test")
        self.assertEqual(restored.messages[1].tool_calls[0].name, "echo")
        self.assertEqual(restored.artifacts[0].mime_type, "application/json")

        result = WorkflowResult(
            messages=[AgentMessage(role="assistant", content="done")],
            artifacts=[Artifact(name="report.txt", data="ok")],
            state={"step": "complete"},
            metadata={"source": "workflow"},
        )

        restored_result = WorkflowResult.from_dict(result.to_dict())
        copy_of_result = restored_result.copy()

        self.assertEqual(restored_result.state["step"], "complete")
        self.assertEqual(copy_of_result.metadata["source"], "workflow")
        self.assertEqual(copy_of_result.messages[0].content, "done")

    def test_spec_models_round_trip(self) -> None:
        provider = ProviderProfile(
            name="openai_compatible",
            family="openai-compatible",
            model="gpt-5",
            description="OpenAI-compatible provider",
            api_base="https://example.com/v1",
            api_key_env="OPENAI_API_KEY",
            supports_streaming=True,
            metadata={"tier": "prod"},
        )
        tool = ToolSpec(
            name="echo",
            summary="Echo text back",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
            output_schema={"type": "string"},
            metadata={"category": "demo"},
        )
        skill = SkillSpec(
            name="research",
            summary="Collect facts",
            instructions="Gather notes before answering.",
            inputs=("topic",),
            outputs=("notes",),
            metadata={"tier": "gold"},
        )
        plugin = PluginSpec(
            name="filesystem",
            version="1.2.3",
            summary="Persist state",
            entrypoint="talosent.plugins.filesystem",
            skills=("research",),
            tools=("echo",),
            metadata={"enabled": True},
        )

        self.assertEqual(ProviderProfile.from_dict(provider.to_dict()), provider)
        self.assertEqual(ToolSpec.from_dict(tool.to_dict()), tool)
        self.assertEqual(SkillSpec.from_dict(skill.to_dict()), skill)
        self.assertEqual(PluginSpec.from_dict(plugin.to_dict()), plugin)

    def test_filesystem_storage_and_persistent_memory_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorageBackend(Path(tmpdir))
            object_ = StorageObject(
                key="blobs/hello.txt",
                data=b"hello world",
                content_type="text/plain",
                metadata={"source": "unit"},
            )

            storage.put(object_)

            reloaded = storage.get("blobs/hello.txt")
            self.assertIsNotNone(reloaded)
            self.assertEqual(reloaded.data, b"hello world")
            self.assertIn("blobs/hello.txt", storage.keys())
            self.assertEqual(storage.items()[0].content_type, "text/plain")

            storage.delete("blobs/hello.txt")
            self.assertIsNone(storage.get("blobs/hello.txt"))

            store = PersistentMemoryStore(storage, namespace="memory")
            entry = MemoryEntry(
                key="topic",
                value={"name": "agents"},
                tags=("research", "notes"),
                metadata={"source": "unit"},
            )
            store.put(entry)

            reloaded_entry = store.get("topic")
            self.assertIsNotNone(reloaded_entry)
            self.assertEqual(reloaded_entry.value["name"], "agents")
            self.assertEqual(store.find_by_tag("research")[0].key, "topic")
            self.assertEqual(len(store.items()), 1)

            store.clear()
            self.assertIsNone(store.get("topic"))

    def test_in_memory_store_helpers(self) -> None:
        store = InMemoryMemoryStore()
        store.upsert_many(
            [
                MemoryEntry(key="alpha", value=1, tags=("one",)),
                MemoryEntry(key="beta", value=2, tags=("two",)),
            ]
        )

        self.assertEqual(store.find_by_tag("two")[0].key, "beta")
        self.assertEqual(len(store), 2)
        store.clear()
        self.assertEqual(len(store.items()), 0)

