# Talosent

Talosent is a modular, provider-agnostic agent runtime with a clean split between core runtime code and launch surfaces. The reusable implementation lives under `src/talosent/`, while repo-local wrappers for interactive entrypoints live under `apps/`.

The repository currently ships with:

- a local heuristic provider for offline development
- an OpenAI-compatible provider for real API calls
- a built-in `current_time` tool
- a terminal UI and a browser UI
- `doctor` and `config` commands for inspecting the runtime

## Design

The project keeps a few simple boundaries:

- `src/talosent/agent/` owns message/state models and workflow orchestration
- `src/talosent/providers/` owns provider profiles, factories, and implementations
- `src/talosent/tools/` owns tool schemas, registration, and built-in tools
- `src/talosent/web/` owns the shared browser UI implementation
- `apps/` owns repo-local launchers, one subdirectory per app

There is intentionally no `src/talosent/apps/` package. Application wrappers stay at the repository root so they do not blur into the core library surface.

## Quick Start

Install the package in editable mode:

```bash
python -m pip install -e .
```

Inspect the resolved configuration:

```bash
talosent config
```

Check the runtime surface:

```bash
talosent doctor
```

Start the terminal UI:

```bash
talosent-tui
```

Start the web UI:

```bash
talosent-web --open-browser
```

If you want to run directly from the repository root without installing the package:

```bash
python -m talosent doctor
python -m apps.tui --prompt "what time is it?"
python -m apps.web --port 8000
```

## Configuration

Talosent reads its settings from environment variables. The defaults are chosen to work locally out of the box.

| Variable | Purpose | Default |
| --- | --- | --- |
| `TALOSENT_APP_NAME` | Human-readable app name | `Talosent` |
| `TALOSENT_ENV` | Runtime environment label | `development` |
| `TALOSENT_LOG_LEVEL` | Logging level | `INFO` |
| `TALOSENT_PROVIDER` | Selected provider profile | `local` |
| `TALOSENT_MODEL` | Model label shown in status and logs | `stub` |
| `TALOSENT_OPENAI_API_KEY` | API key for the OpenAI-compatible provider | empty |
| `TALOSENT_OPENAI_BASE_URL` | Base URL for the OpenAI-compatible provider | `https://api.openai.com/v1` |
| `TALOSENT_MEMORY_BACKEND` | Memory backend label | `in_memory` |
| `TALOSENT_STORAGE_BACKEND` | Storage backend label | `filesystem` |
| `TALOSENT_RECENT_TURNS` | Recent user/assistant turns kept verbatim in the prompt | `4` |
| `TALOSENT_MEMORY_FACT_LIMIT` | Maximum number of extracted key memory facts | `8` |
| `TALOSENT_SUMMARY_TURN_PREVIEW_LIMIT` | Number of dropped turns sampled into the running summary | `8` |
| `TALOSENT_SUMMARY_CHAR_LIMIT` | Maximum characters kept in the summary | `2000` |
| `TALOSENT_API_HOST` | Host used by the web server | `127.0.0.1` |
| `TALOSENT_API_PORT` | Port used by the web server | `8000` |

To use a real provider, set:

```bash
export TALOSENT_PROVIDER=openai_compatible
export TALOSENT_OPENAI_API_KEY=...
export TALOSENT_MODEL=...
```

### Conversation Memory

Talosent keeps a compact prompt by combining three layers:

- recent turns stay verbatim so the model can continue the conversation naturally
- older turns roll into a running summary
- stable facts are extracted into key memory items for long-lived context

If a conversation feels too compressed, increase `TALOSENT_RECENT_TURNS` or `TALOSENT_SUMMARY_CHAR_LIMIT`. If you want the prompt to stay tighter, lower those values.

## Commands

| Command | Description |
| --- | --- |
| `talosent` | Main CLI entrypoint |
| `talosent doctor` | Print a runtime summary |
| `talosent config` | Print resolved settings as JSON |
| `talosent-tui` | Start the terminal chat UI |
| `talosent-web` | Start the browser chat UI |
| `python -m talosent` | Same as `talosent` |
| `python -m apps.tui` | Repo-local TUI wrapper |
| `python -m apps.web` | Repo-local web wrapper |

## Layout

```text
talosent/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ src/
│  └─ talosent/
│     ├─ agent/
│     ├─ cli/
│     ├─ config/
│     ├─ gateway/
│     ├─ memory/
│     ├─ observability/
│     ├─ plugins/
│     ├─ providers/
│     ├─ skills/
│     ├─ storage/
│     ├─ tools/
│     └─ web/
├─ apps/
│  ├─ tui/
│  └─ web/
├─ tests/
├─ evals/
├─ docs/
├─ examples/
├─ scripts/
└─ assets/
```

## Development

Run the test suite:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

The current built-in tool set is intentionally small. If you want to extend the runtime, the usual starting points are:

- `src/talosent/providers/` for new providers
- `src/talosent/tools/` for new tools
- `src/talosent/agent/workflows/` for new workflows
- `src/talosent/web/` for browser UI changes
