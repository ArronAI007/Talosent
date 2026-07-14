"""Repo-local wrapper that makes the TUI runnable from the repository root."""

from __future__ import annotations

from apps._bootstrap import ensure_src_on_path


ensure_src_on_path()

from talosent.cli.tui import main


if __name__ == "__main__":
    raise SystemExit(main())
