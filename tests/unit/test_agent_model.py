from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.agent import AgentContext, WorkflowResult


class AgentModelTests(unittest.TestCase):
    def test_agent_context_collects_messages_and_artifacts(self) -> None:
        context = AgentContext(conversation_id="conv-1")

        message = context.add_message("user", "hello", source="test")
        artifact = context.add_artifact("summary.txt", "hello world", mime_type="text/plain")

        self.assertEqual(context.conversation_id, "conv-1")
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(len(context.artifacts), 1)
        self.assertEqual(message.metadata["source"], "test")
        self.assertEqual(artifact.mime_type, "text/plain")

    def test_workflow_result_applies_to_context(self) -> None:
        context = AgentContext()
        result = WorkflowResult(state={"step": "done"}, metadata={"source": "workflow"})
        result.apply_to(context)

        self.assertEqual(context.state["step"], "done")
        self.assertEqual(context.metadata["source"], "workflow")
