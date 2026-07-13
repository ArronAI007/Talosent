"""Module entrypoint for `python -m talosent`."""

from __future__ import annotations

from talosent.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())

