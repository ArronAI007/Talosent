# TUI App

Repo-local launcher package for the Talosent terminal UI.

This directory is intentionally thin. The actual terminal experience lives in `src/talosent/cli/tui.py`; `apps/tui/` only provides a repo-root-friendly entrypoint and a small amount of usage documentation.

## Files

- `main.py` adds the local `src/` directory to `sys.path` and forwards to the real CLI
- `__main__.py` makes `python -m apps.tui` work
- `__init__.py` keeps the directory a proper Python package
- `README.md` documents the local launcher

## Run

From the repository root:

```bash
python -m apps.tui --prompt "what time is it?"
```

Installed script:

```bash
talosent-tui
```

Interactive mode:

```bash
python -m apps.tui
```

## Options

- `--prompt` sends one prompt, prints the response, and exits
- `--max-turns` sets the provider/tool loop limit for a single turn

## Interactive Commands

- `/exit` or `/quit` leaves the session
- `/reset` clears the in-memory conversation state

