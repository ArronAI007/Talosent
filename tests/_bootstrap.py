"""Test bootstrap helpers."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_src_on_path() -> None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    src_text = str(src_path)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)

