import glob
import json
import unittest
from pathlib import Path

import yaml

from engine.coherence import (
    build_portfolio_coherence,
    format_portfolio_markdown,
    module_coherence,
)
from engine.provenance import build_module_provenance

ROOT = Path(__file__).resolve().parents[1]
MODULE = "gb_finance_data_breach_midmarket"


def _schema_vocabulary():
    schema = json.loads((ROOT / "schemas" / "evidence_record_schema.json").read_text(encoding="utf-8"))
    return set(schema["properties"]["records"]["items"]["properties"]["measurement_basis"]["enum"])


class MeasurementBasisDeclarationTests(unittest.TestCase):
    """ADR-0007 part 1: every record declares what quantity it measures."""

    def setUp(self):
        self.records = []
        for path in sorted(glob.glob(str(ROOT / "evidence" / "*.yaml"))):
            payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
            for record in payload.get("records", []):
                self.records.append((Path(path).name, record))

    def test_every_record_declares_a_measurement_basis(self):
        missing = [
            f"{filename}:{record.get('id')}"
            for filename, record in self.records
            if not record.get("measurement_basis")
        ]
        self.assertEqual(missing, [], f"records without a measurement_basis: {missing}")

    def test_every_declared_basis_is_in_the_controlled_vocabulary(self):
        vocabulary = _schema_vocabulary()
        stray = sorted(
            {
                record.get("measurement_basis")
                for _, record in self.records
                if record.get("measurement_basis") not in vocabulary
            }
        )
        self.assertEqual(stray, [], f"measurement_basis values outside the schema enum: {stray}")

    def test_context_parameters_are_not_treated_as_range_anchors(self):
        """A `context.*` record must never claim a distribution-anchor basis."""
        anchor_bases = {"mean_total_event_cost", "median_total_event_cost", "observed_extremum"}
        offenders = [
            record.get("id")
            for _, record in self.records
            if (record.get("parameter") or "").startswith("context.")
            and record.get("measurement_basis") in anchor_bases
        ]
        self.assertEqual(offenders, [])


class ModuleCoherenceTests(unittest.TestCase):
    def test_gb_impact_is_mixed_across_three_named_bases(self):
        """The worked example in ADR-0007: perceived cost / total loss / regulatory penalty."""
        families = {f["family"]: f for f in module_coherence(build_module_provenance(MODULE, ROOT))}
        impact = families["impact"]
        self.assertEqual(impact["status"], "mixed")
        self.assertEqual(
            sorted(impact["bases"]),
            ["mean_total_event_cost", "perceived_cost_self_reported", "regulatory_penalty_issued"],
        )

    def test_gb_frequency_is_coherent(self):
        families = {f["family"]: f for f in module_coherence(build_module_provenance(MODULE, ROOT))}
        self.assertEqual(families["frequency"]["status"], "coherent")
        self.assertEqual(families["frequency"]["bases"], ["org_prevalence_incident"])

    def test_context_families_are_excluded(self):
        families = [f["family"] for f in module_coherence(build_module_provenance(MODULE, ROOT))]
        self.assertNotIn("context", families)
        self.assertEqual(sorted(families), ["frequency", "impact"])

    def test_single_basis_family_reports_one_basis(self):
        synthetic = {
            "cards": [
                {"parameter": "impact.min", "measurement_basis": "mean_total_event_cost", "value": 1},
                {"parameter": "impact.likely", "measurement_basis": "mean_total_event_cost", "value": 2},
                {"parameter": "impact.max", "measurement_basis": "mean_total_event_cost", "value": 3},
            ]
        }
        result = module_coherence(synthetic)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "coherent")

    def test_undeclared_basis_is_not_silently_coherent(self):
        """A missing basis must surface as `undeclared`, never pass as agreement."""
        synthetic = {
            "cards": [
                {"parameter": "impact.min", "measurement_basis": "mean_total_event_cost", "value": 1},
                {"parameter": "impact.likely", "measurement_basis": None, "value": 2},
            ]
        }
        result = module_coherence(synthetic)
        self.assertEqual(result[0]["status"], "undeclared")
        self.assertEqual(result[0]["unresolved"], ["likely"])


class PortfolioCoherenceTests(unittest.TestCase):
    def setUp(self):
        self.portfolio = build_portfolio_coherence(ROOT)

    def test_totals_are_internally_consistent(self):
        totals = self.portfolio["totals"]
        self.assertEqual(
            totals["families"],
            totals["coherent"] + totals["mixed"] + totals["undeclared"],
        )
        self.assertEqual(totals["shards"], len(self.portfolio["modules"]))

    def test_no_family_is_undeclared(self):
        """Every selected anchor in the portfolio carries a basis."""
        self.assertEqual(self.portfolio["totals"]["undeclared"], 0)

    def test_every_shard_reports_a_frequency_and_impact_family(self):
        for module in self.portfolio["modules"]:
            families = {f["family"] for f in module["families"]}
            self.assertIn("frequency", families, module["module_id"])
            self.assertIn("impact", families, module["module_id"])

    def test_markdown_names_the_bases_of_a_mixed_family(self):
        markdown = format_portfolio_markdown(self.portfolio)
        self.assertIn("Range coherence report", markdown)
        self.assertIn("perceived_cost_self_reported", markdown)
        self.assertIn("mixed", markdown)


class PublishedSurfaceTests(unittest.TestCase):
    """The count has to reach a reader, not just the CLI.

    ADR-0003's lesson was that a caveat only counts where it is published. These
    pin the coherence declaration to the two surfaces a reader actually meets, so
    it cannot quietly drop out of either.
    """

    def test_evidence_report_carries_the_headline_and_a_basis_per_row(self):
        from engine.provenance import build_portfolio_provenance, format_portfolio_markdown as report

        markdown = report(build_portfolio_provenance(ROOT))
        self.assertIn("**Range coherence:**", markdown)
        self.assertIn("| Parameter | Value | Status | Declared for | Fit vs this cell | Measures | Exceedance | Source | Caveat |", markdown)
        self.assertIn("is a mixed range", markdown)
        self.assertIn("`perceived_cost_self_reported`", markdown)

    def test_explorer_payload_carries_basis_coherence_and_totals(self):
        from scripts.build_explorer import build_data

        data = build_data(ROOT)
        totals = data["totals"]
        for key in ("families_coherent", "families_mixed", "families_total"):
            self.assertIn(key, totals)
        self.assertEqual(
            totals["families_total"], totals["families_coherent"] + totals["families_mixed"]
        )

        gb = next(s for s in data["shards"] if s["id"] == "gb_finance_data_breach_midmarket")
        impact = next(f for f in gb["coherence"] if f["family"] == "impact")
        self.assertEqual(impact["status"], "mixed")
        self.assertIn("perceived_cost_self_reported", impact["bases"])
        self.assertTrue(
            all(p.get("basis") for p in gb["params"]),
            "every explorer parameter row must state what it measures",
        )


if __name__ == "__main__":
    unittest.main()
