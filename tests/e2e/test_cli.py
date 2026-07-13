from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO

from tests._bootstrap import ensure_src_on_path

ensure_src_on_path()

from talosent.cli.main import main


class CliE2ETests(unittest.TestCase):
    def test_doctor_command_prints_runtime_summary(self) -> None:
        buffer = StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["doctor"])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Talosent", output)
        self.assertIn("environment:", output)

    def test_config_command_prints_json(self) -> None:
        buffer = StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["config"])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn('"app_name": "Talosent"', output)
