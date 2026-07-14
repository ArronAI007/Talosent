"""Logging configuration for Talosent."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO", *, force: bool = False) -> logging.Logger:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=force,
    )
    return logging.getLogger("talosent")
