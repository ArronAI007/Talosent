"""Allow `python -m apps.tui` from the repository root."""

from __future__ import annotations

from apps.tui.main import main


if __name__ == "__main__":
    raise SystemExit(main())

