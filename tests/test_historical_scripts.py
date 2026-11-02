"""Regression checks for paper-specific public analysis entry points."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HistoricalScriptTests(unittest.TestCase):
    def test_training_log_cli_rejects_missing_root(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/historical/verify_historical_updates.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--root", result.stderr)

    @unittest.skipUnless(
        importlib.util.find_spec("numpy"), "historical analysis extra not installed"
    )
    def test_original_controlled_cases_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "generated"
            command = [
                sys.executable,
                str(ROOT / "scripts/historical/controlled_benchmark.py"),
                "--output",
                str(output),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((output / "summary.json").read_text())
            matrix = summary["metrics"]["combined"]["confusion"]
            self.assertEqual(
                matrix,
                {
                    "PASS": {"PASS": 1, "FAIL": 0, "UNRESOLVED": 0},
                    "FAIL": {"PASS": 0, "FAIL": 10, "UNRESOLVED": 0},
                    "UNRESOLVED": {"PASS": 0, "FAIL": 0, "UNRESOLVED": 5},
                },
            )
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("FileExistsError", again.stderr)


if __name__ == "__main__":
    unittest.main()
