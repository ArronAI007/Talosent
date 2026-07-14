from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentContext, AgentMessage, SequentialWorkflow, WorkflowResult, WorkflowSpec, WorkflowStep
from talosent.gateway import GatewayRegistry, GatewayRequest, GatewayResponse
from talosent.memory import InMemoryMemoryStore, MemoryEntry
from talosent.plugins import PluginRegistry, PluginSpec
from talosent.providers import ProviderProfile, ProviderRegistry
from talosent.skills import SkillRegistry, SkillSpec
from talosent.storage import InMemoryStorageBackend, StorageObject
from talosent.tools import ToolRegistry, ToolSpec


class RegistryIntegrationTests(unittest.TestCase):
    def test_registries_and_backends_round_trip(self) -> None:
        provider_registry = ProviderRegistry()
        provider_registry.register(ProviderProfile(name="local", model="stub"))
        provider_registry.register_many(
            [(ProviderProfile(name="remote", family="openai-compatible", model="gpt-5"), None)]
        )
        self.assertEqual(provider_registry.resolve("local").model, "stub")
        self.assertEqual(provider_registry.describe("local"), "local:stub")
        self.assertIn("local", provider_registry.as_dict())

        tool_registry = ToolRegistry()
        tool_registry.register(ToolSpec(name="echo"), lambda arguments: arguments["text"])
        tool_registry.register_many(
            [(ToolSpec(name="reverse"), lambda arguments: arguments["text"][::-1])]
        )
        self.assertEqual(tool_registry.invoke("echo", {"text": "hello"}), "hello")
        self.assertEqual(tool_registry.get_spec("echo").name, "echo")
        self.assertEqual(tool_registry.describe("echo"), "echo")
        self.assertEqual(tool_registry.invoke("reverse", {"text": "abc"}), "cba")

        skill_registry = SkillRegistry()
        skill_registry.register(SkillSpec(name="research", summary="Collect facts"))
        self.assertEqual(skill_registry.get("research").spec.summary, "Collect facts")
        self.assertEqual(skill_registry.describe("research"), "research: Collect facts")

        plugin_registry = PluginRegistry()
        plugin_registry.register(PluginSpec(name="filesystem", entrypoint="talosent.plugins.filesystem"))
        self.assertEqual(
            plugin_registry.get("filesystem").spec.entrypoint,
            "talosent.plugins.filesystem",
        )
        self.assertEqual(plugin_registry.describe("filesystem"), "filesystem 0.1.0")

        memory_store = InMemoryMemoryStore()
        memory_store.put(MemoryEntry(key="topic", value="agents"))
        self.assertEqual(memory_store.get("topic").value, "agents")

        storage_backend = InMemoryStorageBackend()
        storage_backend.put(StorageObject(key="blob.txt", data=b"hello"))
        self.assertEqual(storage_backend.get("blob.txt").data, b"hello")

        gateway_registry = GatewayRegistry()

        class EchoGateway:
            name = "echo"

            def send(self, request: GatewayRequest) -> GatewayResponse:
                return GatewayResponse(ok=True, payload=request.payload)

        gateway_registry.register(EchoGateway())
        response = gateway_registry.dispatch(GatewayRequest(channel="echo", payload={"text": "hi"}))
        self.assertTrue(response.ok)
        self.assertEqual(response.payload["text"], "hi")

    def test_sequential_workflow_merges_results(self) -> None:
        context = AgentContext()

        def first_step(current: AgentContext) -> WorkflowResult:
            return WorkflowResult(
                messages=[AgentMessage(role="assistant", content="step 1")],
                state={"step": 1},
            )

        def second_step(current: AgentContext) -> WorkflowResult:
            return WorkflowResult(
                messages=[AgentMessage(role="assistant", content="step 2")],
                metadata={"final": True},
            )

        workflow = SequentialWorkflow(
            spec=WorkflowSpec(name="sequential-demo"),
            steps=(
                WorkflowStep(name="first", handler=first_step),
                WorkflowStep(name="second", handler=second_step),
            ),
        )

        result = workflow.run(context)

        self.assertEqual(result.state["step"], 1)
        self.assertTrue(result.metadata["final"])
        self.assertEqual(len(context.messages), 2)
