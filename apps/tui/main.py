"""Repo-local wrapper that makes the TUI runnable from the repository root."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


_ensure_src_on_path()

from talosent.cli.tui import main


if __name__ == "__main__":
    raise SystemExit(main())
