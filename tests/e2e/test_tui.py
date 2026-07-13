from __future__ import annotations

import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.cli.tui import main


class TuiE2ETests(unittest.TestCase):
    def test_prompt_mode_runs_tool_loop(self) -> None:
        buffer = StringIO()

        with patch.dict(os.environ, {"TALOSENT_PROVIDER": "local"}, clear=True):
            with redirect_stdout(buffer):
                exit_code = main(["--prompt", "what time is it?"])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Talosent TUI | provider=local", output)
        self.assertIn("assistant> requesting tool: current_time", output)
        self.assertIn("tool[current_time]>", output)
        self.assertIn("The current time in UTC is", output)
