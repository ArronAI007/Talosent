# Architecture

Talosent is a modular, provider-agnostic agent runtime. The core library lives in `src/talosent/` and has no third-party dependencies. Runnable surfaces (CLI, TUI, web) are thin wrappers built on top of the same runtime.

## Request Flow

```text
user input
    │
    ▼
apps/ (tui, web)            repo-local launchers, argument parsing only
    │
    ▼
talosent/cli/               entry points, logging setup, server bootstrap
    │
    ▼
talosent/runtime.py         composition root: settings + provider + tools + workflow
    │
    ▼
talosent/agent/workflows/   ChatWorkflow: agent loop (provider ⇄ tools), memory refresh
    │
    ├──────────────► talosent/providers/   LLM calls (ChatProvider protocol)
    │
    ├──────────────► talosent/tools/       tool execution (ToolRegistry)
    │
    └──────────────► talosent/memory/      session persistence + prompt compression
```

## Module Boundaries

| Module | Owns | Must not do |
| --- | --- | --- |
| `agent/` | Message/state models (`AgentMessage`, `AgentContext`), workflow orchestration | Call providers directly outside workflows |
| `providers/` | `ChatProvider` protocol, provider profiles, registry, implementations | Know about tools or workflows |
| `tools/` | `ToolSpec` schemas, `ToolRegistry`, built-in tools | Call LLMs |
| `memory/` | Conversation memory (recent turns + summary + key facts), persistent stores | Own provider calls |
| `storage/` | `StorageBackend` implementations (in-memory, filesystem) | Know about agent semantics |
| `skills/` | Reusable `SkillSpec` definitions and registry | Execute anything |
| `plugins/` | Optional `PluginSpec` packages grouping skills/tools | Load code dynamically |
| `gateway/` | Contracts for external channels (`GatewayAdapter` protocol) | Implement channel logic in core |
| `config/` | Environment-backed `Settings` | Hold runtime state |
| `observability/` | Logging configuration | Own business logic |
| `web/` | HTTP server and HTML rendering for the browser UI | Own workflow logic |
| `cli/` | `talosent`, `talosent-tui`, `talosent-web` entry points | Contain reusable logic |

## Composition Root

`talosent/runtime.py` is the only place that wires settings → provider → tools → workflow. Surfaces (`cli/web.py`, `cli/tui.py`, `web/server.py`) call `build_chat_workflow()` and never construct providers or registries themselves. Tests inject fakes through the same parameters.

## Agent Loop

`ChatWorkflow.run()` iterates up to `max_turns`:

1. Refresh the prompt context (system prompt + memory summary + recent turns).
2. Call `provider.complete(messages, tools)`.
3. If the response has content, record it as the assistant message.
4. If the response has tool calls, execute each via `ToolRegistry.invoke()` and append tool messages; loop again.
5. Stop when the provider returns no tool calls, then persist the session.

## Conversation Memory

Three layers keep the prompt compact:

- **Recent turns** stay verbatim (`recent_turns`, default 4).
- **Dropped turns** roll into a running summary (`summary_char_limit`, default 2000).
- **Stable facts** (name, location, preferences, project goals) are extracted with pattern matching into key memory items (`memory_fact_limit`, default 8).

Sessions persist through `PersistentMemoryStore` on a `StorageBackend`, keyed by `sessions/<workflow>/<conversation_id>`.

## Provider Contract

```python
class ChatProvider(Protocol):
    def complete(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec] = (),
    ) -> ProviderResponse: ...
```

`ProviderResponse` carries optional `content` and optional `tool_calls`. A provider never executes tools; it only requests them. This keeps the loop testable with scripted fakes (see `tests/integration/test_chat_workflow.py`).

## Error Handling

- Provider exceptions are caught in the workflow, recorded as an assistant error message, and surfaced in `result.state["error"]`.
- Tool exceptions are caught per call and returned to the provider as `ERROR: ...` tool messages so the model can recover.
- The web layer maps workflow failures to HTTP 500 with a JSON error body.

## Surfaces

| Surface | Entry | Notes |
| --- | --- | --- |
| CLI | `talosent` / `python -m talosent` | `doctor` and `config` inspection commands |
| TUI | `talosent-tui` / `python -m apps.tui` | Terminal chat via `rich` |
| Web | `talosent-web` / `python -m apps.web` | stdlib `http.server`, single-page UI from `web/page.py` |

The web UI is server-rendered HTML with embedded CSS/JS. There is no frontend build step; keep it that way unless a real bundler is introduced deliberately.
