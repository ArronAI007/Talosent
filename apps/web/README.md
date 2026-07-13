# Web App

Repo-local launcher for the Talosent browser UI.

Run it from the repository root with:

```bash
python -m apps.web --host 127.0.0.1 --port 8000
```

You can also use the installed script:

```bash
talosent-web --open-browser
```

The launcher stays separate from `src/talosent/` so browser-facing code remains optional and the core runtime stays clean.
