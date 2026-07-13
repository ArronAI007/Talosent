# Talosent

Talosent is a small, clean starting point for a general-purpose agent project.

The codebase is organized so the responsibilities stay separate:

- `src/talosent/agent/` holds agent state and workflow orchestration
- `src/talosent/providers/` holds provider profiles and provider registration
- `src/talosent/tools/` holds tool schemas and tool dispatch
- `src/talosent/skills/` holds reusable, declarative skill definitions
- `src/talosent/plugins/` holds optional extension packages
- `src/talosent/gateway/` holds external channel and protocol adapters
- `src/talosent/memory/` and `src/talosent/storage/` hold persistence abstractions
- `src/talosent/cli/` holds the command-line entrypoint
- `apps/` is reserved for future UIs such as web and TUI surfaces

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

## Layout

```text
talosent/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ src/
│  └─ talosent/
│     ├─ agent/
│     ├─ providers/
│     ├─ tools/
│     ├─ skills/
│     ├─ plugins/
│     ├─ gateway/
│     ├─ memory/
│     ├─ storage/
│     ├─ cli/
│     ├─ config/
│     └─ observability/
├─ apps/
│  ├─ web/
│  └─ tui/
├─ tests/
├─ evals/
├─ docs/
├─ examples/
├─ scripts/
└─ assets/
```

