"""HTTP server and request handling for the Talosent web UI."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from talosent.agent.model import AgentContext, AgentMessage, Artifact, ToolCall
from talosent.agent.workflows import ChatWorkflow
from talosent.config import Settings, load_settings
from talosent.providers import ChatProvider
from talosent.runtime import build_chat_workflow
from talosent.tools import ToolRegistry, build_tool_registry
from talosent.web.page import render_home_page

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TalosentWebApplication:
    settings: Settings
    workflow: ChatWorkflow
    sessions: dict[str, AgentContext] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    @property
    def provider_name(self) -> str:
        return getattr(self.workflow.provider, "name", self.workflow.provider.__class__.__name__)

    @property
    def tool_names(self) -> tuple[str, ...]:
        return self.workflow.tools.names()

    def health_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "app_name": self.settings.app_name,
            "provider": self.provider_name,
            "model": self.settings.default_model,
            "tools": list(self.tool_names),
            "active_sessions": len(self.sessions),
        }

    def get_session(self, conversation_id: str | None = None) -> AgentContext:
        with self.lock:
            if conversation_id and conversation_id in self.sessions:
                return self.sessions[conversation_id]

            session = AgentContext(conversation_id=conversation_id or uuid4().hex)
            self.sessions[session.conversation_id] = session
            return session

    def handle_chat(self, conversation_id: str | None, message: str) -> dict[str, Any]:
        session = self.get_session(conversation_id)
        session.add_message("user", message)
        result = self.workflow.run(session)

        return {
            "ok": True,
            "conversation_id": session.conversation_id,
            "reply": result.state.get("final_message", ""),
            "state": result.state,
            "messages": [_serialize_message(item) for item in session.messages],
            "artifacts": [_serialize_artifact(item) for item in result.artifacts],
            "provider": result.state.get("provider", self.provider_name),
            "tools": list(self.tool_names),
        }


class TalosentWebServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], RequestHandlerClass, app: TalosentWebApplication):
        super().__init__(server_address, RequestHandlerClass)
        self.web_app = app


class TalosentWebHandler(BaseHTTPRequestHandler):
    server_version = "TalosentWeb/0.1"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        app = self._app()

        if route in {"/", "/index.html"}:
            html = render_home_page(
                app.settings.app_name,
                app.provider_name,
                app.settings.default_model,
                app.tool_names,
            )
            self._send_html(html)
            return

        if route == "/api/health":
            self._send_json(app.health_payload())
            return

        self._send_json({"ok": False, "error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path

        if route != "/api/chat":
            self._send_json({"ok": False, "error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        message = str(payload.get("message") or "").strip()
        if not message:
            self._send_json({"ok": False, "error": "message is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        conversation_id = payload.get("conversation_id")
        conversation_id = str(conversation_id).strip() if conversation_id else None

        try:
            response = self._app().handle_chat(conversation_id, message)
        except Exception as exc:  # pragma: no cover - defensive fallback
            LOGGER.exception("chat request failed")
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json(response)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        LOGGER.debug("%s - %s", self.address_string(), format % args)

    def _app(self) -> TalosentWebApplication:
        return self.server.web_app  # type: ignore[attr-defined]

    def _read_json(self) -> dict[str, Any]:
        length_raw = self.headers.get("Content-Length", "0")
        try:
            length = int(length_raw)
        except ValueError as exc:
            raise ValueError("invalid Content-Length header") from exc

        body = self.rfile.read(length) if length else b""
        if not body:
            return {}

        try:
            payload = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError("request body must be utf-8 encoded JSON") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("request body must be valid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def create_web_server(
    settings: Settings | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    provider: ChatProvider | None = None,
    tools: ToolRegistry | None = None,
    max_turns: int = 4,
) -> TalosentWebServer:
    runtime_settings = settings or load_settings()
    runtime_tools = tools or build_tool_registry()
    workflow = build_chat_workflow(
        runtime_settings,
        provider=provider,
        tools=runtime_tools,
        max_turns=max_turns,
    )
    application = TalosentWebApplication(settings=runtime_settings, workflow=workflow)
    server = TalosentWebServer(
        (host or runtime_settings.api_host, port if port is not None else runtime_settings.api_port),
        TalosentWebHandler,
        application,
    )
    return server


def _serialize_message(message: AgentMessage) -> dict[str, Any]:
    return {
        "role": message.role,
        "content": message.content,
        "name": message.name,
        "tool_call_id": message.tool_call_id,
        "tool_calls": [_serialize_tool_call(call) for call in message.tool_calls],
        "metadata": dict(message.metadata),
    }


def _serialize_tool_call(tool_call: ToolCall) -> dict[str, Any]:
    return {
        "id": tool_call.id,
        "name": tool_call.name,
        "arguments": dict(tool_call.arguments),
    }


def _serialize_artifact(artifact: Artifact) -> dict[str, Any]:
    return {
        "name": artifact.name,
        "data": artifact.data,
        "mime_type": artifact.mime_type,
        "metadata": dict(artifact.metadata),
    }
