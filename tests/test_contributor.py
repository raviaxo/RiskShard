import tempfile
import unittest
from pathlib import Path

from engine.contributor import (
    build_contributor_preflight,
    format_contributor_preflight,
    scaffold_contributor_pack,
)


ROOT = Path(__file__).resolve().parents[1]


class ContributorTests(unittest.TestCase):
    def test_contributor_preflight_summarizes_pack_readiness(self):
        preflight = build_contributor_preflight(ROOT)
        output = format_contributor_preflight(preflight)

        self.assertEqual(preflight["status"], "pass")
        self.assertIn("source registry", {item["name"] for item in preflight["checks"]})
        self.assertIn("data pack fingerprint", {item["name"] for item in preflight["checks"]})
        self.assertIn("Contributor preflight", output)
        self.assertIn("evidence quality: pass", output)

    def test_contributor_preflight_validates_proposed_pack_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "example_pack"
            build_example_pack(pack)

            preflight = build_contributor_preflight(ROOT, pack_path=pack)
            output = format_contributor_preflight(preflight)

        self.assertEqual(preflight["status"], "pass")
        self.assertIn("Pack:", output)
        self.assertIn("pack evidence: pass", output)
        self.assertIn("pack calibration: pass", output)
        self.assertIn("pack risk module: pass", output)
        self.assertIn("benchmark target mapping: pass", output)

    def test_contributor_preflight_reports_missing_pack_pieces(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "incomplete_pack"
            (pack / "evidence").mkdir(parents=True)

            preflight = build_contributor_preflight(ROOT, pack_path=pack)
            output = format_contributor_preflight(preflight)

        self.assertEqual(preflight["status"], "fail")
        self.assertIn("missing sources, evidence, extractions, calibrations, risk_modules", output)

    def test_contributor_scaffold_creates_pack_and_warns_on_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "ca_pack"
            result = scaffold_contributor_pack(
                ROOT,
                pack,
                module_id="ca_finance_data_breach_midmarket",
                country="CA",
                industry="financial_services",
                company_size="mid_market",
                threat="data_breach",
                title="Canada Finance Data Breach Midmarket",
            )
            preflight = build_contributor_preflight(ROOT, pack_path=pack)
            output = format_contributor_preflight(preflight)

        self.assertEqual(result["status"], "created")
        self.assertIn("risk_modules/ca_finance_data_breach_midmarket.yaml", result["files"])
        self.assertEqual(preflight["status"], "needs_review")
        self.assertIn("placeholder review: warn", output)
        self.assertIn("benchmark target mapping: pass", output)


def build_example_pack(pack):
    for folder in [
        "sources",
        "evidence",
        "extractions",
        "calibrations",
        "risk_modules",
        "scenarios",
        "org_profiles",
    ]:
        (pack / folder).mkdir(parents=True)
    (pack / "README.md").write_text("Example pack for contributor preflight tests.\n")
    (pack / "sources" / "registry.yaml").write_text(
        "sources:\n"
        "  - id: example_pack_source\n"
        "    title: Example Pack Source\n"
        "    publisher: Example Publisher\n"
        "    source_type: official_statistics\n"
        "    url: https://example.com/risk-pack-source\n"
        "    publication_date: '2026-06-01'\n"
        "    access_mode: public_html\n"
        "    intended_use: [testing]\n"
        "    usage_notes: Contributor preflight fixture.\n"
    )
    evidence_records = []
    for parameter, value in [
        ("frequency.min", 0.1),
        ("frequency.likely", 0.2),
        ("frequency.max", 0.3),
        ("impact.min", 10000),
        ("impact.likely", 20000),
        ("impact.max", 30000),
    ]:
        unit = "currency" if parameter.startswith("impact") else "annual_probability"
        currency = "\n    currency: USD" if unit == "currency" else ""
        evidence_records.append(
            f"  - id: example_{parameter.replace('.', '_')}\n"
            f"    title: Example {parameter}\n"
            f"    parameter: {parameter}\n"
            f"    value: {value}\n"
            f"    unit: {unit}{currency}\n"
            f"    source_id: example_pack_source\n"
            f"    source_name: Example Pack Source\n"
            f"    source_type: official_statistics\n"
            f"    source_url_or_citation: https://example.com/risk-pack-source\n"
            f"    publication_date: '2026-06-01'\n"
            f"    extraction_date: '2026-06-15'\n"
            f"    citation_detail: Fixture citation for {parameter}.\n"
            f"    extraction_notes: Fixture extraction.\n"
            f"    normalization_notes: Fixture normalization.\n"
            f"    limitations: Fixture only.\n"
            f"    confidence: low\n"
            f"    evidence_type: source_backed\n"
            f"    measurement_basis: "
            f"{'mean_total_event_cost' if unit == 'currency' else 'org_prevalence_incident'}\n"
            # ADR-0008: the schema requires an exceedance declaration on any maximum.
            + ("    exceedance_basis: none_known\n" if parameter == "impact.max" else "")
            + f"    population_match:\n"
            f"      status: matched\n"
            f"    applicability:\n"
            f"      industries: [financial_services]\n"
            f"      countries: [CA]\n"
            f"      company_size_bands: [mid_market]\n"
            f"      threats: [data_breach]\n"
        )
    (pack / "evidence" / "example_pack.yaml").write_text("records:\n" + "\n".join(evidence_records))
    (pack / "extractions" / "example_pack_reviewed.yaml").write_text(
        "extractions:\n"
        "  - id: example_pack_extraction\n"
        "    source_id: example_pack_source\n"
        "    source_name: Example Pack Source\n"
        "    source_url_or_citation: https://example.com/risk-pack-source\n"
        "    publication_date: '2026-06-01'\n"
        "    extraction_date: '2026-06-15'\n"
        "    citation_detail: Fixture citation.\n"
        "    fact: Example source supports all fixture values.\n"
        "    value: 1\n"
        "    unit: count\n"
        "    normalization_notes: Fixture normalization.\n"
        "    limitations: Fixture only.\n"
        "    evidence_record_ids:\n"
        "      - example_frequency_min\n"
        "      - example_frequency_likely\n"
        "      - example_frequency_max\n"
        "      - example_impact_min\n"
        "      - example_impact_likely\n"
        "      - example_impact_max\n"
    )
    (pack / "calibrations" / "example_pack.yaml").write_text(
        "metadata:\n"
        "  name: Example pack calibration\n"
        "target_currency: USD\n"
        "parameters:\n"
        "  frequency:\n"
        "    min: {evidence_id: example_frequency_min, transform: direct}\n"
        "    likely: {evidence_id: example_frequency_likely, transform: direct}\n"
        "    max: {evidence_id: example_frequency_max, transform: direct}\n"
        "  impact:\n"
        "    min: {evidence_id: example_impact_min, transform: direct, target_currency: USD}\n"
        "    likely: {evidence_id: example_impact_likely, transform: direct, target_currency: USD}\n"
        "    max: {evidence_id: example_impact_max, transform: direct, target_currency: USD}\n"
    )
    (pack / "scenarios" / "example_pack.yaml").write_text(
        "metadata:\n"
        "  name: Example Pack\n"
        "  version: '0.1'\n"
        "frequency: {min: 0.1, likely: 0.2, max: 0.3}\n"
        "impact: {min: 10000, likely: 20000, max: 30000}\n"
    )
    (pack / "org_profiles" / "example_pack.yaml").write_text(
        "metadata:\n"
        "  name: Example Org\n"
        "industry: financial_services\n"
        "country: CA\n"
        "employees: 500\n"
        "revenue: 100000000\n"
        "company_size: mid_market\n"
        "regulatory_intensity: medium\n"
    )
    (pack / "risk_modules" / "example_pack.yaml").write_text(
        "id: ca_finance_data_breach_midmarket\n"
        "title: Canada Finance Data Breach Midmarket\n"
        "version: '0.1'\n"
        "status: governed_starter\n"
        "threat: data_breach\n"
        "context:\n"
        "  industry: financial_services\n"
        "  country: CA\n"
        "  company_size: mid_market\n"
        "artifacts:\n"
        "  scenario: scenarios/example_pack.yaml\n"
        "  org_profile: org_profiles/example_pack.yaml\n"
        "  calibration: calibrations/example_pack.yaml\n"
        "  evidence: [evidence/example_pack.yaml]\n"
        "  extractions: [extractions/example_pack_reviewed.yaml]\n"
        "required_parameters: [frequency.min, frequency.likely, frequency.max, impact.min, impact.likely, impact.max]\n"
    )


if __name__ == "__main__":
    unittest.main()
