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

# ADR-0003 portfolio-provenance totals — the v0.2.0 headline split.
POP_TOTALS = {"params_cell_matched": 28, "params_cross_cell": 38, "params_cross_country": 26}


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


class PopulationSplitTests(unittest.TestCase):
    """ADR-0003: the split arrives as a separate input (the readiness matrix has
    no population data) and must never fabricate a delta against entries that
    predate it."""

    def test_snapshot_records_the_split_when_totals_are_given(self):
        snap = capture_snapshot(_dashboard(IMPROVED_MATRIX, "abc"), population_totals=POP_TOTALS)
        m = snap["metrics"]
        self.assertEqual(m["params_cell_matched"], 28)
        self.assertEqual(m["params_cross_cell"], 38)
        self.assertEqual(m["params_cross_country"], 26)

    def test_snapshot_omits_the_split_without_totals(self):
        m = capture_snapshot(_dashboard(IMPROVED_MATRIX, "abc"))["metrics"]
        self.assertNotIn("params_cell_matched", m)
        self.assertNotIn("params_cross_cell", m)
        self.assertNotIn("params_cross_country", m)

    def test_delta_omits_split_keys_the_prior_entry_never_measured(self):
        prev = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))["metrics"]
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"), population_totals=POP_TOTALS)["metrics"]
        delta = compute_delta(prev, curr)
        self.assertEqual(delta["params_source_backed"], 2)  # base keys still compared
        self.assertNotIn("params_cell_matched", delta)      # no fabricated "+28"

    def test_delta_compares_split_keys_when_both_entries_carry_them(self):
        prev = capture_snapshot(_dashboard(IMPROVED_MATRIX, "abc"), population_totals=POP_TOTALS)["metrics"]
        later = {"params_cell_matched": 32, "params_cross_cell": 34, "params_cross_country": 22}
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"), population_totals=later)["metrics"]
        delta = compute_delta(prev, curr)
        self.assertEqual(delta["params_cell_matched"], 4)
        self.assertEqual(delta["params_cross_cell"], -4)
        self.assertEqual(delta["params_cross_country"], -4)

    def test_coherence_split_records_and_never_fabricates_a_delta(self):
        """ADR-0007's split, folded in at the v0.5.0 cut, obeys the ADR-0003 rule.

        The coherence layer names its totals `coherent`/`mixed`; the ledger stores
        them prefixed. Entries that predate the split must read "newly measured",
        never "+4 coherent" against an entry that never counted families.
        """
        coh = {"coherent": 4, "mixed": 18, "undeclared": 0, "families": 22}
        curr = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "def"), population_totals=POP_TOTALS, coherence_totals=coh
        )["metrics"]
        self.assertEqual(curr["families_coherent"], 4)
        self.assertEqual(curr["families_mixed"], 18)

        pre_split = capture_snapshot(_dashboard(IMPROVED_MATRIX, "abc"), population_totals=POP_TOTALS)
        self.assertNotIn("families_coherent", pre_split["metrics"])
        delta = compute_delta(pre_split["metrics"], curr)
        self.assertIn("params_cell_matched", delta)      # the older split still compares
        self.assertNotIn("families_coherent", delta)     # no fabricated "+4"
        self.assertNotIn("families_mixed", delta)

        later = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "ghi"),
            population_totals=POP_TOTALS,
            coherence_totals={"coherent": 9, "mixed": 13},
        )["metrics"]
        self.assertEqual(compute_delta(curr, later)["families_coherent"], 5)

    def test_tail_split_records_and_never_fabricates_a_delta(self):
        """ADR-0008's split, folded in at v0.6.0 — third axis, same rule as the first two.

        Three splits have now been added at three releases. Each must read "newly
        measured" on arrival and compare normally afterwards; an entry from before an
        axis existed must never receive a delta on it.
        """
        coh = {"coherent": 4, "mixed": 18}
        tail = {"quantified": 2, "none_known": 7, "shards_majority_driven_by_max": 7}
        curr = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "def"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
            tail_totals=tail,
        )["metrics"]
        self.assertEqual(curr["maxima_quantified"], 2)
        self.assertEqual(curr["maxima_none_known"], 7)
        self.assertEqual(curr["shards_tail_driven"], 7)

        pre_tail = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "abc"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
        )
        self.assertNotIn("maxima_quantified", pre_tail["metrics"])
        delta = compute_delta(pre_tail["metrics"], curr)
        self.assertIn("families_coherent", delta)       # the v0.5.0 axis compares
        self.assertNotIn("maxima_quantified", delta)    # the v0.6.0 axis is newly measured
        self.assertNotIn("shards_tail_driven", delta)

        later = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "ghi"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
            tail_totals={"quantified": 5, "none_known": 4, "shards_majority_driven_by_max": 5},
        )["metrics"]
        moved = compute_delta(curr, later)
        self.assertEqual(moved["maxima_quantified"], 3)
        self.assertEqual(moved["maxima_none_known"], -3)
        self.assertEqual(moved["shards_tail_driven"], -2)

    def test_slot_split_records_and_never_fabricates_a_delta(self):
        """The anchor-slot axis, folded in at v0.7.0 — fourth axis, same rule again.

        Four splits at four consecutive releases. The guard is the point: an entry
        recorded before an axis existed must never receive a delta on it, because a
        delta against a release that never measured the thing is a fabricated
        improvement.
        """
        coh = {"coherent": 4, "mixed": 18}
        tail = {"quantified": 2, "none_known": 7, "shards_majority_driven_by_max": 7}
        slots = {
            "shards": 11,
            "mode_slot_declarations": 11,
            "shards_mode_slot_central_tendency": 8,
            "shards_floor_slot": 7,
        }
        curr = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "def"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
            tail_totals=tail,
            slot_totals=slots,
        )["metrics"]
        self.assertEqual(curr["likely_anchors"], 11)
        self.assertEqual(curr["likely_not_a_mode"], 11)
        self.assertEqual(curr["likely_central_tendency"], 8)
        self.assertEqual(curr["floor_central_tendency"], 7)

        pre_slot = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "abc"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
            tail_totals=tail,
        )
        self.assertNotIn("likely_not_a_mode", pre_slot["metrics"])
        delta = compute_delta(pre_slot["metrics"], curr)
        self.assertIn("maxima_quantified", delta)        # the v0.6.0 axis compares
        self.assertNotIn("likely_not_a_mode", delta)     # the v0.7.0 axis is newly measured
        self.assertNotIn("likely_central_tendency", delta)
        self.assertNotIn("floor_central_tendency", delta)

        later = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "ghi"),
            population_totals=POP_TOTALS,
            coherence_totals=coh,
            tail_totals=tail,
            slot_totals={**slots, "shards_mode_slot_central_tendency": 6,
                         "shards_floor_slot": 5},
        )["metrics"]
        moved = compute_delta(curr, later)
        self.assertEqual(moved["likely_central_tendency"], -2)
        self.assertEqual(moved["floor_central_tendency"], -2)
        self.assertEqual(moved["likely_not_a_mode"], 0)

    def test_the_likely_denominator_is_recorded_not_inferred(self):
        """The v0.6.0 cut shipped a line reading '2 of 9' because the denominator was
        inferred from the categories that happened to be named. The count of likely
        anchors is its own recorded key for exactly that reason."""
        from engine.strength_ledger import SLOT_KEYS

        self.assertIn("likely_anchors", SLOT_KEYS)
        metrics = capture_snapshot(
            _dashboard(IMPROVED_MATRIX, "def"),
            slot_totals={
                "shards": 11,
                "mode_slot_declarations": 11,
                "shards_mode_slot_central_tendency": 8,
                "shards_floor_slot": 7,
            },
        )["metrics"]
        self.assertEqual(metrics["likely_anchors"], 11)
        self.assertNotEqual(
            metrics["likely_anchors"],
            metrics["likely_central_tendency"] + metrics["floor_central_tendency"],
            "the denominator must not coincide with a sum of the buckets beside it",
        )

    def test_markdown_shows_a_dash_for_pre_split_entries(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            ledger = Path(tmp.name) / "l.json"
            record_snapshot(ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "v0.1.0-test")
            record_snapshot(
                ledger,
                _dashboard(IMPROVED_MATRIX, "def"),
                "2026-08-01",
                "v0.2.0-test",
                population_totals=POP_TOTALS,
            )
            md = format_progress_markdown(ledger)
            self.assertIn("Cell-matched", md)
            self.assertIn("| — |", md)   # the pre-split row
            self.assertIn("| 28 |", md)  # the split row, no fabricated delta
        finally:
            tmp.cleanup()


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
            self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test"
        )
        self.assertTrue(appended)
        self.assertIsNone(delta)
        self.assertEqual(entry["date"], "2026-07-24")
        self.assertEqual(len(load_ledger(self.ledger)), 1)

    def test_recording_without_a_release_version_is_refused(self):
        """The ledger records releases, not every pack edit.

        The rule was documented as "on release only" but implemented as "fingerprint
        differs", and a fingerprint moves on any pack edit. That produced nine entries
        between 2026-07-24 and 2026-07-30 of which one matched an actual release.
        """
        with self.assertRaises(ValueError):
            record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "")
        self.assertEqual(load_ledger(self.ledger), [])

    def test_unchanged_fingerprint_is_a_noop(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
        entry, appended, _ = record_snapshot(
            self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-31", "2026-07-31-test"
        )
        self.assertFalse(appended)
        self.assertEqual(len(load_ledger(self.ledger)), 1)  # not padded

    def test_new_release_appends_and_reports_delta(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
        entry, appended, delta = record_snapshot(
            self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31", "2026-07-31-test"
        )
        self.assertTrue(appended)
        self.assertEqual(delta["params_source_backed"], 2)
        self.assertEqual(delta["params_bridged"], -2)
        self.assertEqual(len(load_ledger(self.ledger)), 2)

    def test_ledger_file_is_structured_json(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 1)

    def test_latest_delta_tracks_the_last_two_entries(self):
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
        record_snapshot(self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31", "2026-07-31-test")
        latest, delta = latest_delta(self.ledger)
        self.assertEqual(latest["fingerprint"], "def")
        self.assertEqual(delta["params_source_backed"], 2)


class TrendAndBaselineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self._tmp.name) / "strength_ledger.json"
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
        record_snapshot(self.ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31", "2026-07-31-test")

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
            record_snapshot(ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
            self.assertEqual(baseline_delta(ledger), (None, None))
        finally:
            tmp.cleanup()

    def test_markdown_table_lists_newest_first_with_delta(self):
        md = format_progress_markdown(self.ledger)
        self.assertIn("| Release | Date |", md)
        # newest (def) row appears before the baseline (abc) row
        self.assertLess(md.index("2026-07-31"), md.index("2026-07-24"))
        self.assertIn("66 / 66 (+2)", md)

    def test_a_recorded_note_reaches_the_rendered_table(self):
        """The field existed and nothing rendered it — that is the defect this pins.

        A `note` sat on the 2026-07-24 entry from the day it was written until
        2026-08-15 and no reader ever saw it, because `format_progress_markdown`
        only ever emitted metrics. A note explains why a number moved, so a note
        that renders nowhere is worse than absent: it reads as recorded.
        """
        tmp = tempfile.TemporaryDirectory()
        try:
            ledger = Path(tmp.name) / "l.json"
            record_snapshot(ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24",
                            "2026-07-24-test")
            entry, appended, _ = record_snapshot(
                ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31", "2026-07-31-test",
                note="the measurement changed, not the evidence",
            )
            self.assertTrue(appended)
            self.assertEqual(entry["note"], "the measurement changed, not the evidence")
            md = format_progress_markdown(ledger)
            self.assertIn("the measurement changed, not the evidence", md)
            # attributed to its release, and below the table rather than inside it
            self.assertIn("**2026-07-31-test —**", md)
            self.assertLess(md.index("| --- |"), md.index("the measurement changed"))
        finally:
            tmp.cleanup()

    def test_note_is_labelled_by_release_not_the_repeating_pack_version(self):
        """`data_pack_version` repeats — the real ledger has two `2026.07.24` rows.

        Labelling a note with it would leave a reader unable to tell which row the
        explanation belongs to, which is most of a note's value.
        """
        tmp = tempfile.TemporaryDirectory()
        try:
            ledger = Path(tmp.name) / "l.json"
            record_snapshot(ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24",
                            "2026-07-24-test")
            record_snapshot(ledger, _dashboard(IMPROVED_MATRIX, "def"), "2026-07-31",
                            "2026-07-31-test", note="why it moved")
            versions = {e["data_pack_version"] for e in load_ledger(ledger)}
            self.assertEqual(len(versions), 1)      # both entries share a pack version
            self.assertIn("**2026-07-31-test —**", format_progress_markdown(ledger))
        finally:
            tmp.cleanup()

    def test_an_entry_without_a_note_adds_nothing(self):
        self.assertNotIn(" —** ", format_progress_markdown(self.ledger))


class ReadmeWriterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self._tmp.name) / "strength_ledger.json"
        record_snapshot(self.ledger, _dashboard(BASELINE_MATRIX, "abc"), "2026-07-24", "2026-07-24-test")
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

    def test_split_rows_render_and_pre_split_delta_says_newly_measured(self):
        prev = capture_snapshot(_dashboard(BASELINE_MATRIX, "abc"))["metrics"]
        curr = capture_snapshot(_dashboard(IMPROVED_MATRIX, "def"), population_totals=POP_TOTALS)["metrics"]
        out = "\n".join(_format_strength({"metrics": curr, "delta": compute_delta(prev, curr)}))
        self.assertIn("cell-matched: 28 (newly measured)", out)
        self.assertIn("population-bridged: 38 (newly measured)", out)

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
