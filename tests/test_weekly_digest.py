import unittest

from engine.weekly_digest import _summarize_state, format_weekly_digest


SAMPLE_DASHBOARD = {
    "risk_modules": {"module_count": 11},
    "top_risks": [
        {"status": "calibrated"},
        {"status": "calibrated"},
        {"status": "calibrated_with_assumptions"},
        {"status": "partially_supported"},
    ],
    "localization": {"covered_countries": ["US", "GB", "all"]},
    "evidence_packs": {
        "coverage_matrix": [
            {"source_backed_direct": 6, "direct_total": 6},
            {"source_backed_direct": 4, "direct_total": 6},
        ]
    },
    "data_pack": {"fingerprint": "abc123"},
}


class SummarizeStateTests(unittest.TestCase):
    def test_summarizes_dashboard_fields(self):
        state = _summarize_state(SAMPLE_DASHBOARD)
        self.assertEqual(state["shards"], 11)
        self.assertEqual(state["shards_fully_sourced"], 1)
        self.assertEqual(state["countries"], 2)  # 'all' excluded
        self.assertEqual(state["top_risks_total"], 4)
        # both 'calibrated' and 'calibrated_with_assumptions' are runnable
        self.assertEqual(state["top_risks_runnable"], 3)


class FormatTests(unittest.TestCase):
    def _digest(self, shipped, contributors):
        return {
            "since_days": 7,
            "state": _summarize_state(SAMPLE_DASHBOARD),
            "shipped": shipped,
            "contributors": contributors,
        }

    def test_full_digest_has_sections_and_fill_blanks(self):
        out = format_weekly_digest(
            self._digest(["#42 feat-insider", "#43 feat-tpo"], ["Sergio Alonso", "Jane Doe"]),
            week_of="Jul 21",
            owner_name="Sergio Alonso",
        )
        self.assertIn("Shard Notes — Week of Jul 21", out)
        self.assertIn("11 shards", out)
        self.assertIn("3/4 top risks runnable", out)
        self.assertIn("#42 feat-insider", out)
        self.assertIn("Jane Doe", out)
        self.assertNotIn("Sergio Alonso", out)  # owner filtered from the community line
        self.assertIn("Lesson: <fill>", out)
        self.assertIn("Next: <fill>", out)

    def test_quiet_week_has_graceful_fallbacks(self):
        out = format_weekly_digest(self._digest([], []))
        self.assertIn("quiet week", out)
        self.assertIn("issues are open", out)

    def _digest_with_strength(self, note):
        digest = self._digest([], [])
        digest["strength"] = {
            "metrics": {"params_source_backed": 66, "shards_fully_sourced": 11,
                        "params_bridged": 0, "params_cell_matched": 7,
                        "params_cross_cell": 59},
            "delta": {"params_source_backed": 0, "shards_fully_sourced": 0,
                      "params_bridged": 0, "params_cell_matched": -24,
                      "params_cross_cell": 24},
            "note": note,
        }
        return digest

    def test_a_falling_count_goes_out_with_its_reason(self):
        """This is the one surface that goes *out* rather than waiting to be visited.

        v0.8.0 sent `cell-matched: 31 -> 7 (-24)` on evidence where not one
        parameter, source, value or caveat had changed. A subscriber reading that
        without the release's ledger note learns the opposite of what happened.
        """
        out = format_weekly_digest(
            self._digest_with_strength("the measurement changed, not the evidence")
        )
        self.assertIn("cell-matched: 31 -> 7 (-24)", out)
        self.assertIn("why: the measurement changed, not the evidence", out)
        self.assertLess(out.index("cell-matched: 31"), out.index("why:"))

    def test_a_note_is_flattened_for_a_plain_text_surface(self):
        """The note is authored in Markdown for the README table; this is not that.

        A relative link is not even resolvable once the digest is pasted into a post
        or an email, so it becomes its own text rather than shipping as syntax.
        """
        out = format_weekly_digest(self._digest_with_strength(
            "**7** is what *cell-matched* always was — see "
            "[finding 6](docs/FINDINGS.md)."
        ))
        self.assertIn("why: 7 is what cell-matched always was — see finding 6.", out)
        for syntax in ("**", "](", "docs/FINDINGS.md"):
            self.assertNotIn(syntax, out)

    def test_a_release_without_a_note_adds_no_why_line(self):
        self.assertNotIn("why:", format_weekly_digest(self._digest_with_strength(None)))


if __name__ == "__main__":
    unittest.main()
