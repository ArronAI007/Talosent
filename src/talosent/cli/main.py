"""CLI for inspecting the Talosent runtime surface."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from talosent import __version__
from talosent.config import load_settings
from talosent.observability import configure_logging
from talosent.runtime import build_provider, build_tool_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="talosent",
        description="Talosent agent runtime utilities.",
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Print a quick runtime summary.")
    subparsers.add_parser("config", help="Print the resolved settings as JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.log_level)

    if args.command == "doctor":
        provider = build_provider(settings)
        tools = build_tool_registry()
        print(f"Talosent {__version__}")
        print(f"environment: {settings.environment}")
        print(f"selected provider: {provider.name}")
        print(f"model: {settings.default_model}")
        print(f"memory backend: {settings.memory_backend}")
        print(f"storage backend: {settings.storage_backend}")
        print(f"tools: {', '.join(tools.names()) or '(none)'}")
        return 0

    if args.command == "config":
        print(json.dumps(settings.to_dict(), indent=2, sort_keys=True))
        return 0

    parser.print_help()
    return 0
