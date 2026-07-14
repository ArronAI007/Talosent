"""Shared helpers for repo-local app launchers."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path() -> None:
    """Make the repository's ``src`` directory importable for local launchers."""
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
