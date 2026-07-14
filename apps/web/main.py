"""Repo-local wrapper that makes the web UI runnable from the repository root."""

from __future__ import annotations

from apps._bootstrap import ensure_src_on_path


ensure_src_on_path()

from talosent.cli.web import main


if __name__ == "__main__":
    raise SystemExit(main())
