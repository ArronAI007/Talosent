from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.config import load_settings
from talosent.gateway import GatewayRequest, GatewayResponse
from talosent.plugins import PluginSpec
from talosent.runtime import build_runtime
from talosent.skills import SkillSpec


class RuntimeBundleTests(unittest.TestCase):
    def test_runtime_bundle_exposes_all_core_surfaces(self) -> None:
        settings = load_settings({"TALOSENT_PROVIDER": "local", "TALOSENT_MODEL": "stub"})
        runtime = build_runtime(settings)

        self.assertEqual(runtime.provider_name, "local")
        self.assertIn("current_time", runtime.tool_names)
        self.assertEqual(runtime.summary()["memory_entries"], 0)

        runtime.skills.register_many([SkillSpec(name="research", summary="Collect facts")])
        runtime.plugins.register_many(
            [PluginSpec(name="filesystem", entrypoint="talosent.plugins.filesystem")]
        )

        class EchoGateway:
            name = "echo"

            def send(self, request: GatewayRequest) -> GatewayResponse:
                return GatewayResponse(ok=True, payload=request.payload)

        runtime.gateways.register_many([EchoGateway()])
        responses = runtime.gateways.dispatch_many(
            [GatewayRequest(channel="echo", payload={"hello": "world"})]
        )

        summary = runtime.summary()
        self.assertEqual(responses[0].payload["hello"], "world")
        self.assertIn("research", summary["skills"])
        self.assertIn("filesystem", summary["plugins"])
        self.assertIn("echo", summary["gateways"])

