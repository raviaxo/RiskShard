import unittest

from engine import coverage


def summary(source_backed, assumptions, missing, confidence="medium", freshness="current"):
    return {
        "source_backed_direct": source_backed,
        "assumption_only_direct": assumptions,
        "missing_direct": missing,
        "direct_total": source_backed + assumptions + missing,
        "pack_confidence": confidence,
        "freshness_status": freshness,
    }


class GradeShardTests(unittest.TestCase):
    def test_all_source_backed_is_source_backed(self):
        grade = coverage.grade_shard(summary(6, 0, 0, confidence="high"))
        self.assertEqual(grade["grade"], "source_backed")
        self.assertIn("high confidence", grade["label"])

    def test_some_assumptions_is_bridged(self):
        grade = coverage.grade_shard(summary(4, 2, 0))
        self.assertEqual(grade["grade"], "bridged")

    def test_any_missing_is_provisional(self):
        grade = coverage.grade_shard(summary(3, 2, 1))
        self.assertEqual(grade["grade"], "provisional")

    def test_no_confidence_or_all_missing_is_scaffold(self):
        self.assertEqual(coverage.grade_shard(summary(0, 0, 6))["grade"], "scaffold")
        self.assertEqual(
            coverage.grade_shard(summary(2, 0, 0, confidence="none"))["grade"],
            "scaffold",
        )

    def test_stale_feed_raises_flag_but_does_not_change_grade(self):
        grade = coverage.grade_shard(summary(6, 0, 0, freshness="needs_source_review"))
        self.assertEqual(grade["grade"], "source_backed")
        self.assertTrue(any("stale-feeds" in flag for flag in grade["flags"]))

    def test_grade_never_claims_benchmark(self):
        for name in coverage.GRADES:
            self.assertNotIn("benchmark", coverage.GRADES[name]["label"].lower())


class CoverageReportTests(unittest.TestCase):
    def test_report_sorts_strongest_first_and_counts(self):
        report = coverage.build_coverage_report()
        ranks = [item["grade"]["rank"] for item in report["shards"]]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(sum(report["grade_counts"].values()), report["shard_count"])

    def test_format_names_the_ledger_and_gate(self):
        report = coverage.build_coverage_report()
        text = coverage.format_coverage_report(report)
        self.assertIn("ledger", text.lower())
        self.assertIn("benchmark_program.py", text)
        self.assertIn("Where to contribute", text)

    def test_render_coverage_html_is_self_contained_and_branded(self):
        report = coverage.build_coverage_report()
        html = coverage.render_coverage_html(report)
        self.assertTrue(html.lstrip().startswith("<!doctype html>"))
        self.assertIn("Coverage &amp; Confidence", html)
        self.assertIn("Where you can help", html)
        self.assertIn("High-confidence", html)
        # self-contained: styles inline, no external resource loads
        self.assertIn("<style>", html)
        self.assertNotIn("http://", html.replace("http://www.w3.org", ""))


if __name__ == "__main__":
    unittest.main()
