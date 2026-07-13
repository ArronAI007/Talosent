"""Allow `python -m apps.web` from the repository root."""

from __future__ import annotations

from apps.web.main import main


if __name__ == "__main__":
    raise SystemExit(main())

