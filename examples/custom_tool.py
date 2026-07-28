"""Register a custom tool and run a full agent loop with a scripted provider.

Run from the repository root:

    python examples/custom_tool.py

The scripted provider requests the custom ``word_count`` tool once, receives
the tool result, and answers with it — no network or API key required.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talosent.agent import AgentContext, ToolCall
from talosent.agent.workflows import ChatWorkflow, WorkflowSpec
from talosent.providers import ProviderResponse
from talosent.tools import ToolSpec, build_tool_registry

GREETING = "hello from the talosent runtime"


def word_count(arguments: dict[str, Any]) -> dict[str, Any]:
    """Count words and characters in a text snippet."""
    text = str(arguments.get("text") or "")
    return {"text": text, "words": len(text.split()), "chars": len(text)}


WORD_COUNT_SPEC = ToolSpec(
    name="word_count",
    summary="Count words and characters in a text snippet.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to measure."},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
)


class ScriptedProvider:
    """Deterministic stand-in for an LLM: request the tool, then summarize."""

    name = "scripted"

    def complete(self, messages, tools=()):
        tool_message = next((m for m in reversed(messages) if m.role == "tool"), None)
        if tool_message is None:
            return ProviderResponse(
                tool_calls=(
                    ToolCall(
                        id=uuid4().hex,
                        name="word_count",
                        arguments={"text": GREETING},
                    ),
                ),
            )
        payload = json.loads(tool_message.content)
        return ProviderResponse(
            content=f"'{payload['text']}' has {payload['words']} words and {payload['chars']} characters."
        )


def main() -> int:
    registry = build_tool_registry()  # built-ins, e.g. current_time
    registry.register(WORD_COUNT_SPEC, word_count)

    workflow = ChatWorkflow(
        spec=WorkflowSpec(name="custom-tool-example"),
        provider=ScriptedProvider(),
        tools=registry,
    )

    context = AgentContext()
    context.add_message("user", "How many words are in my greeting?")
    result = workflow.run(context)

    print(f"provider: {result.state['provider']}")
    print(f"turns:    {result.state['turns']}")
    print(f"reply:    {result.state['final_message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
