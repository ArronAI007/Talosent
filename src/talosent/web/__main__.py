"""Allow `python -m talosent.web` to start the web server."""

from __future__ import annotations

from talosent.cli.web import main


if __name__ == "__main__":
    raise SystemExit(main())

