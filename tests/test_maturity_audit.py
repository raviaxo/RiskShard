import unittest

from engine import maturity_audit


class ClassifyTests(unittest.TestCase):
    def test_gate_ready_but_plain_label_is_under_labeled(self):
        self.assertEqual(
            maturity_audit.classify("governed_starter", "benchmark_ready"),
            "under_labeled",
        )

    def test_claiming_label_but_gate_not_ready_is_over_labeled(self):
        self.assertEqual(
            maturity_audit.classify("benchmark_candidate", "needs_evidence"),
            "over_labeled",
        )

    def test_aligned_cases_are_consistent(self):
        self.assertEqual(
            maturity_audit.classify("benchmark_candidate", "benchmark_ready"),
            "consistent",
        )
        self.assertEqual(
            maturity_audit.classify("governed_starter", "needs_evidence"),
            "consistent",
        )

    def test_missing_gate_status_is_no_gate(self):
        self.assertEqual(maturity_audit.classify("governed_starter", None), "no_gate")


class ReportTests(unittest.TestCase):
    def test_audit_reports_shape_and_is_read_only(self):
        report = maturity_audit.audit_maturity_labels()
        self.assertEqual(report["module_count"], len(report["modules"]))
        self.assertEqual(report["mismatch_count"], len(report["mismatches"]))
        for row in report["modules"]:
            self.assertIn(
                row["verdict"],
                {"consistent", "under_labeled", "over_labeled", "no_gate"},
            )
        text = maturity_audit.format_maturity_audit(report)
        self.assertIn("changes no labels", text)


if __name__ == "__main__":
    unittest.main()
