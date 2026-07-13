"""Command-line launcher for the Talosent web UI."""

from __future__ import annotations

import argparse
import webbrowser
from collections.abc import Sequence

from talosent.config import load_settings
from talosent.observability import configure_logging
from talosent.web import create_web_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="talosent-web",
        description="Start the Talosent web UI.",
    )
    parser.add_argument("--host", help="Bind host. Defaults to TALOSENT_API_HOST.")
    parser.add_argument("--port", type=int, help="Bind port. Defaults to TALOSENT_API_PORT.")
    parser.add_argument(
        "--max-turns",
        type=int,
        default=4,
        help="Maximum provider/tool turns per chat request.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the browser after the server starts.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.log_level)
    server = create_web_server(
        settings,
        host=args.host or settings.api_host,
        port=args.port if args.port is not None else settings.api_port,
        max_turns=args.max_turns,
    )

    host, port = server.server_address
    display_host = _display_host(args.host or host)
    url = f"http://{display_host}:{port}"
    app = server.web_app

    print(
        f"Talosent Web | provider={app.provider_name} | model={app.settings.default_model} | tools={', '.join(app.tool_names) or '(none)'}"
    )
    print(f"Listening on {url}")

    if args.open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.shutdown()
        server.server_close()

    return 0


def _display_host(host: str) -> str:
    if host in {"0.0.0.0", "::", ""}:
        return "127.0.0.1"
    return host

