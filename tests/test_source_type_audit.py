import unittest
from pathlib import Path

from engine.source_type_audit import (
    audit_source_types,
    classify_source_type,
    load_source_type_taxonomy,
)


ROOT = Path(__file__).resolve().parents[1]


class SourceTypeAuditTests(unittest.TestCase):
    def test_all_source_types_conform_to_vocabulary(self):
        report = audit_source_types(ROOT)
        self.assertEqual(
            report["unknown"],
            [],
            f"Non-conformant source_type values (add to base, use a "
            f"bridge/derived/assumption convention, or reconcile): {report['unknown']}",
        )

    def test_classification_recognizes_base_and_conventions(self):
        taxonomy = load_source_type_taxonomy()
        self.assertEqual(classify_source_type("industry_survey", taxonomy), "base")
        self.assertEqual(classify_source_type("industry_survey_bridge", taxonomy), "bridge")
        self.assertEqual(classify_source_type("derived_statistical_benchmark", taxonomy), "derived")
        self.assertEqual(classify_source_type("model_assumption", taxonomy), "assumption")
        self.assertEqual(classify_source_type("totally_made_up_type", taxonomy), "unknown")

    def test_reconciled_duplicates_are_gone(self):
        report = audit_source_types(ROOT)
        for retired in ("official_statistical_data", "secondary_news_report", "regulatory_statute"):
            self.assertNotIn(retired, report["counts"])
