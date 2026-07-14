from __future__ import annotations

import json
import socket
import threading
import time
import unittest
from contextlib import closing
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.config import load_settings
from talosent.web import create_web_server


class WebE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = load_settings({"TALOSENT_PROVIDER": "local", "TALOSENT_MODEL": "stub"})
        self.server = create_web_server(self.settings, host="127.0.0.1", port=0, max_turns=4)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://{self.server.server_address[0]}:{self.server.server_address[1]}"
        self._wait_until_ready()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_health_page_and_chat_round_trip(self) -> None:
        root_html = self._get_text("/")
        self.assertIn("Talosent Web", root_html)
        self.assertIn("current_time", root_html)

        health = self._get_json("/api/health")
        self.assertEqual(health["provider"], "local")
        self.assertIn("current_time", health["tools"])

        first_reply = self._post_json(
            "/api/chat",
            {"message": "what time is it?"},
        )
        self.assertTrue(first_reply["reply"].startswith("The current time in UTC is"))
        self.assertTrue(any(message["role"] == "tool" for message in first_reply["messages"]))

        conversation_id = first_reply["conversation_id"]
        with self.server.web_app.lock:
            self.server.web_app.sessions.clear()

        second_reply = self._post_json(
            "/api/chat",
            {"conversation_id": conversation_id, "message": "hello again"},
        )
        self.assertEqual(second_reply["conversation_id"], conversation_id)
        self.assertEqual(second_reply["reply"], "You said: hello again")
        self.assertTrue(any(message["role"] == "tool" for message in second_reply["messages"]))
        self.assertTrue(
            any(
                message["role"] == "assistant" and message["content"].startswith("The current time in UTC is")
                for message in second_reply["messages"]
            )
        )

    def _wait_until_ready(self) -> None:
        host, port = self.server.server_address
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                with closing(socket.create_connection((host, port), timeout=0.1)):
                    return
            except OSError:
                time.sleep(0.05)
        self.fail("web server did not become ready")

    def _get_text(self, path: str) -> str:
        with urlopen(f"{self.base_url}{path}") as response:
            return response.read().decode("utf-8")

    def _get_json(self, path: str) -> dict[str, object]:
        with urlopen(f"{self.base_url}{path}") as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
