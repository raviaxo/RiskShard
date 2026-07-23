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


if __name__ == "__main__":
    unittest.main()
