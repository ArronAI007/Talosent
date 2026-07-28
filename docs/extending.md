# Extending Talosent

This guide covers the three common extension points: providers, tools, and workflows. All examples run against the local package without extra dependencies.

## Add a Tool

Tools are a `ToolSpec` (schema) plus a handler function, registered on a `ToolRegistry`.

```python
from typing import Any

from talosent.tools import ToolRegistry, ToolSpec, build_tool_registry


def word_count(arguments: dict[str, Any]) -> dict[str, Any]:
    text = str(arguments.get("text") or "")
    return {"words": len(text.split())}


word_count_spec = ToolSpec(
    name="word_count",
    summary="Count the words in a text snippet.",
    input_schema={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
        "additionalProperties": False,
    },
)

registry = build_tool_registry()          # starts with built-ins (current_time)
registry.register(word_count_spec, word_count)
```

Pass the registry into the runtime via `build_chat_workflow(tools=registry)` or `create_web_server(tools=registry)`.

Rules:

- Keep handlers pure and synchronous; raise `ValueError` for bad input — the workflow converts exceptions into `ERROR: ...` tool messages so the model can recover.
- Give every argument a JSON Schema description; providers use it to decide when to call the tool.
- Add tests in `tests/unit/` for the handler and in `tests/integration/` for the registry wiring.

See `examples/custom_tool.py` for a complete runnable version.

## Add a Provider

A provider implements the `ChatProvider` protocol:

```python
from collections.abc import Sequence

from talosent.agent.model import AgentMessage
from talosent.providers.runtime import ProviderResponse
from talosent.tools.spec import ToolSpec


class MyProvider:
    name = "my-provider"

    def complete(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec] = (),
    ) -> ProviderResponse:
        # Call your LLM API here. Return content, tool_calls, or both.
        return ProviderResponse(content="...")
```

To make it selectable via `TALOSENT_PROVIDER`, register it in `src/talosent/providers/factory.py`:

```python
registry.register(
    ProviderProfile(
        name="my-provider",
        family="my-family",
        model=settings.default_model,
        description="My provider.",
    ),
    lambda profile: MyProvider(...),
)
```

Rules:

- A provider never executes tools. Return `tool_calls` in the response; the workflow executes them and feeds results back.
- Read credentials from `Settings`/environment, never hardcode them.
- If the provider needs a third-party SDK, discuss it first — the core library is dependency-free by design.

## Add a Workflow

Workflows orchestrate the agent loop. Subclass or mirror `ChatWorkflow` in `src/talosent/agent/workflows/`:

```python
from dataclasses import dataclass

from talosent.agent.model import AgentContext, WorkflowResult
from talosent.agent.workflows.base import WorkflowSpec


@dataclass(slots=True)
class MyWorkflow:
    spec: WorkflowSpec

    def run(self, context: AgentContext) -> WorkflowResult:
        result = WorkflowResult()
        # ... orchestrate provider calls, tools, memory
        return result
```

Rules:

- Keep workflow logic free of HTTP/CLI concerns; surfaces adapt to it.
- Store session state through `MemoryStore`, not module-level globals.
- Write an integration test with a scripted fake provider (see `tests/integration/test_chat_workflow.py`) rather than hitting real APIs.

## Add a Surface

Repo-local launchers live in `apps/<name>/` and follow the existing pattern:

- `apps/<name>/main.py` — imports `apps._bootstrap.ensure_src_on_path()` first, then delegates to a `talosent.cli.<name>:main` entry point.
- `apps/<name>/__main__.py` — allows `python -m apps.<name>`.
- `apps/<name>/README.md` — how to run it.

Keep launchers thin: parse arguments, call into `src/talosent/`, print, exit.
