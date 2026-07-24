import json
import tempfile
import unittest
from pathlib import Path

from engine.strength_ledger import (
    baseline_delta,
    capture_snapshot,
    compute_delta,
    format_progress_markdown,
    latest_delta,
    load_ledger,
    record_snapshot,
    trend,
    update_readme_progress,
)
from engine.weekly_digest import _format_strength


def _dashboard(matrix, fingerprint, version="2026.07.24", status_counts=None):
    return {
        "evidence_packs": {"coverage_matrix": matrix},
        "risk_modules": {
            "module_count": len(matrix),
            "status_counts": status_counts or {},
        },
        "data_pack": {"pack_version": version, "fingerprint": fingerprint},
    }


# 10 fully-sourced shards + 1 at 4/6 (2 bridged) — the v0.1.0 shape.
BASELINE_MATRIX = (
    [{"source_backed_direct": 6, "assumption_only_direct": 0, "missing_direct": 0, "direct_total": 6}] * 10
    + [{"source_backed_direct": 4, "assumption_only_direct": 2, "missing_direct": 0, "direct_total": 6}]
)
# The JP shard closed: now 11/11 fully sourced, 0 bridged.
IMPROVED_MATRIX = [{"source_backed_direct": 6, "assumption_only_direct": 0, "missing_direct": 0, "direct_total": 6}] * 11


class CaptureTests(unittest.TestCase):
    def test_snapshot_sums_the_matrix(self):
        snap = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc123"))
        m = snap["metrics"]
        self.assertEqual(m["params_source_backed"], 64)  # 10*6 + 4
        self.assertEqual(m["params_bridged"], 2)
        self.assertEqual(m["params_missing"], 0)
        self.assertEqual(m["params_total"], 66)
        self.assertEqual(m["shards"], 11)
        self.assertEqual(m["shards_fully_sourced"], 10)
        self.assertEqual(snap["fingerprint"], "abc123")


class DeltaTests(unittest.TestCase):
    def test_delta_is_none_without_prior(self):
        self.assertIsNone(compute_delta(None, {"params_source_backed": 64}))

    def test_delta_is_current_minus_previous(self):
        prev = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))["metrics"]
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"))["metrics"]
        delta = compute_delta(prev, curr)
        self.assertEqual(delta["params_source_backed"], 2)   # 66 - 64
        self.assertEqual(delta["params_bridged"], -2)        # 0 - 2
        self.assertEqual(delta["shards_fully_sourced"], 1)   # 11 - 10


class RecordTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self._tmp.name) / "strength_ledger.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_first_record_is_baseline_with_no_delta(self):
        entry, appended, delta = record_snapshot(
            self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24"
        )
        self.assertTrue(appended)
        self.assertIsNone(delta)
        self.assertEqual(entry["date"], "2026-07-24")
        self.assertEqual(len(load_ledger(self.ledger)), 1)

    def test_unchanged_fingerprint_is_a_noop(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        entry, appended, _ = record_snapshot(
            self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-31"
        )
        self.assertFalse(appended)
        self.assertEqual(len(load_ledger(self.ledger)), 1)  # not padded

    def test_new_release_appends_and_reports_delta(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        entry, appended, delta = record_snapshot(
            self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31"
        )
        self.assertTrue(appended)
        self.assertEqual(delta["params_source_backed"], 2)
        self.assertEqual(delta["params_bridged"], -2)
        self.assertEqual(len(load_ledger(self.ledger)), 2)

    def test_ledger_file_is_structured_json(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 1)

    def test_latest_delta_tracks_the_last_two_entries(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        record_snapshot(self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31")
        latest, delta = latest_delta(self.ledger)
        self.assertEqual(latest["fingerprint"], "def")
        self.assertEqual(delta["params_source_backed"], 2)


class TrendAndBaselineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self._tmp.name) / "strength_ledger.json"
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        record_snapshot(self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31")

    def tearDown(self):
        self._tmp.cleanup()

    def test_trend_pairs_each_entry_with_its_delta(self):
        rows = trend(self.ledger)
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[0][1])                       # baseline has no delta
        self.assertEqual(rows[1][1]["params_source_backed"], 2)

    def test_baseline_delta_is_cumulative_from_first(self):
        first, delta = baseline_delta(self.ledger)
        self.assertEqual(first["fingerprint"], "abc")
        self.assertEqual(delta["params_source_backed"], 2)
        self.assertEqual(delta["params_bridged"], -2)

    def test_baseline_delta_none_with_single_entry(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            ledger = Path(tmp.name) / "l.json"
            record_snapshot(ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
            self.assertEqual(baseline_delta(ledger), (None, None))
        finally:
            tmp.cleanup()

    def test_markdown_table_lists_newest_first_with_delta(self):
        md = format_progress_markdown(self.ledger)
        self.assertIn("| Release | Date |", md)
        # newest (def) row appears before the baseline (abc) row
        self.assertLess(md.index("2026-07-31"), md.index("2026-07-24"))
        self.assertIn("66 / 66 (+2)", md)


class ReadmeWriterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self._tmp.name) / "strength_ledger.json"
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24")
        self.readme = Path(self._tmp.name) / "README.md"

    def tearDown(self):
        self._tmp.cleanup()

    def test_rewrites_between_markers(self):
        self.readme.write_text(
            "# Title\n\n<!-- strength-ledger:begin -->\nSTALE\n<!-- strength-ledger:end -->\n\nrest\n",
            encoding="utf-8",
        )
        changed = update_readme_progress(self.readme, self.ledger)
        self.assertTrue(changed)
        out = self.readme.read_text(encoding="utf-8")
        self.assertNotIn("STALE", out)
        self.assertIn("| Release | Date |", out)
        self.assertIn("rest", out)  # content after the end marker preserved

    def test_missing_markers_raises(self):
        self.readme.write_text("# Title\n\nno markers here\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            update_readme_progress(self.readme, self.ledger)


class DigestRenderTests(unittest.TestCase):
    def test_baseline_block_has_no_arrows(self):
        snap = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))
        out = "\n".join(_format_strength({"metrics": snap["metrics"], "delta": None}))
        self.assertIn("Strength (baseline):", out)
        self.assertIn("source-backed params: 64", out)
        self.assertNotIn("->", out)

    def test_delta_block_shows_prev_to_curr(self):
        prev = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))["metrics"]
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"))["metrics"]
        out = "\n".join(_format_strength({"metrics": curr, "delta": compute_delta(prev, curr)}))
        self.assertIn("source-backed params: 64 -> 66 (+2)", out)
        self.assertIn("bridged / estimated: 2 -> 0 (-2)", out)

    def test_since_baseline_line_when_present(self):
        prev = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))["metrics"]
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"))["metrics"]
        out = "\n".join(
            _format_strength(
                {
                    "metrics": curr,
                    "delta": compute_delta(prev, curr),
                    "since_baseline": compute_delta(prev, curr),
                    "baseline_version": "2026.07.24",
                }
            )
        )
        self.assertIn("since 2026.07.24: +2 source-backed params, -2 bridged", out)


if __name__ == "__main__":
    unittest.main()
