# TUI App

Repo-local launcher for the Talosent terminal UI.

Run it from the repository root with:

```bash
python -m apps.tui --prompt "what time is it?"
```

You can also use the installed script:

```bash
talosent-tui
```

The launcher stays separate from `src/talosent/` so terminal-facing code remains an optional surface and the core runtime stays clean.
