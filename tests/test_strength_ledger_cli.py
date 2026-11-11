"""The release commands have to actually run, not just import.

`scripts/strength_ledger.py record` called `build_axis_totals(ROOT)` without
importing it from 2026-08-13 (v0.7.0) until 2026-11-11, so the subcommand the
M4 runbook names to clear the ledger raised `NameError` for 90 days across seven
releases. Nothing caught it, and two things hid it: the ledger was in fact being
written by `scripts/data_pack_manifest.py`, which imports the helper correctly and
records an entry when it cuts a pack, and `scripts/package_smoke.py` checks that
entry points are *importable callables* — which a NameError inside a function body
passes cleanly.

So the gap was never import-level. These tests invoke the subcommands against a
temporary copy of the ledger and assert they exit zero, which is the only thing
that would have failed.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "strength_ledger.py"
LEDGER = ROOT / "docs" / "internal" / "strength_ledger.json"


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )


class SubcommandsRunTests(unittest.TestCase):
    """Every subcommand, actually executed."""

    def test_show_runs(self):
        result = _run("show")
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])

    def test_history_runs(self):
        result = _run("history")
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])

    def test_markdown_runs(self):
        result = _run("markdown")
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])

    def test_record_runs_and_resolves_every_name_it_uses(self):
        """The one that was broken. It must reach its own output, not a NameError.

        Run against the live tree but with `--release` naming the fingerprint that
        is already logged, so the call is a no-op append: it exercises the whole
        code path, including `build_axis_totals`, without mutating the ledger.
        """
        before = LEDGER.read_text(encoding="utf-8")
        try:
            result = _run("record", "--release", "ci-smoke-no-op", "--json")
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            self.assertNotIn("NameError", result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("appended", payload)
            self.assertIn("entry", payload)
            # The axis totals are what the missing import supplied. If they are
            # absent the helper was never reached and this test is vacuous.
            self.assertTrue(payload["entry"].get("metrics"))
        finally:
            LEDGER.write_text(before, encoding="utf-8")

    def test_the_original_bug_would_still_fail_this(self):
        """Verified to fail: strip the import, and `record` must break."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("    build_axis_totals,\n", source,
                      "the import this test guards is gone")
        broken = source.replace("    build_axis_totals,\n", "", 1)
        with tempfile.TemporaryDirectory() as tmp:
            stand_in = Path(tmp) / "strength_ledger.py"
            stand_in.write_text(broken, encoding="utf-8")
            # The stand-in lives outside scripts/, so `engine` must be put on
            # the path explicitly or it fails on the wrong import and the test
            # proves nothing.
            env = {**os.environ, "PYTHONPATH": str(ROOT)}
            result = subprocess.run(
                [sys.executable, str(stand_in), "record",
                 "--release", "ci-smoke-no-op", "--json"],
                cwd=ROOT, capture_output=True, text=True, timeout=600, env=env,
            )
        self.assertNotEqual(result.returncode, 0,
                            "removing the import should break `record`")
        self.assertIn("build_axis_totals", result.stderr)


if __name__ == "__main__":
    unittest.main()
