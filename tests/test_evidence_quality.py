import tempfile
import unittest
from pathlib import Path

from engine.evidence_quality import has_errors, validate_evidence_quality, validate_record_quality


ROOT = Path(__file__).resolve().parents[1]


class EvidenceQualityTests(unittest.TestCase):
    def test_current_evidence_has_no_quality_errors(self):
        issues = validate_evidence_quality(
            ROOT / "evidence",
            ROOT / "sources" / "manifest.json",
        )

        self.assertFalse(has_errors(issues), issues)

    def test_source_backed_evidence_requires_source_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_evidence.yaml"
            path.write_text(
                "records:\n"
                "  - id: bad_source_backed_record\n"
                "    title: Bad source-backed record\n"
                "    parameter: frequency.likely\n"
                "    value: 0.5\n"
                "    unit: annual_probability\n"
                "    source_name: Example\n"
                "    source_type: report\n"
                "    source_url_or_citation: https://example.com\n"
                "    publication_date: '2026-01-01'\n"
                "    extraction_date: '2026-05-26'\n"
                "    extraction_notes: test\n"
                "    normalization_notes: test\n"
                "    limitations: test\n"
                "    confidence: low\n"
                "    evidence_type: source_backed\n"
                "    measurement_basis: org_prevalence_incident\n"
                "    population_match:\n"
                "      status: matched\n"
                "    applicability:\n"
                "      industries: [all]\n"
                "      countries: [global]\n"
                "      company_size_bands: [all]\n"
                "      threats: [all]\n"
            )

            issues = validate_evidence_quality(path, ROOT / "sources" / "manifest.json")

        self.assertTrue(has_errors(issues))
        self.assertIn("source_id_missing", {issue["code"] for issue in issues})

    def test_unfetched_manifest_source_requires_disclosure(self):
        record = {
            "id": "record_with_unfetched_source",
            "title": "Record with unfetched source",
            "parameter": "frequency.min",
            "value": 0.1,
            "unit": "annual_probability",
            "source_id": "example_source",
            "source_name": "Example Source",
            "source_type": "report",
            "source_url_or_citation": "https://example.com/report",
            "publication_date": "2026-01-01",
            "extraction_date": "2026-05-26",
            "citation_detail": "Example section.",
            "extraction_notes": "test",
            "normalization_notes": "test",
            "limitations": "No disclosure.",
            "confidence": "low",
            "evidence_type": "source_backed",
            "applicability": {
                "industries": ["all"],
                "countries": ["global"],
                "company_size_bands": ["all"],
                "threats": ["all"],
            },
        }
        manifest = {
            "example_source": {
                "id": "example_source",
                "url": "https://example.com/report",
                "final_url": None,
                "publication_date": "2026-01-01",
                "status": "error",
            }
        }

        issues = validate_record_quality(record, manifest)

        self.assertIn("source_not_fetched", {issue["code"] for issue in issues})
        self.assertIn("source_not_fetched_not_disclosed", {issue["code"] for issue in issues})

    def test_multi_source_records_must_include_known_sources_and_primary_source(self):
        record = {
            "id": "multi_source_record",
            "title": "Multi-source record",
            "parameter": "frequency.min",
            "value": 0.1,
            "unit": "annual_probability",
            "source_id": "source_a",
            "source_ids": ["source_b", "missing_source"],
            "source_name": "Example Sources",
            "source_type": "derived_benchmark",
            "source_url_or_citation": "https://example.com/a",
            "publication_date": "2026-01-01",
            "extraction_date": "2026-05-26",
            "citation_detail": "Example section.",
            "extraction_notes": "test",
            "normalization_notes": "test",
            "limitations": "test",
            "confidence": "low",
            "evidence_type": "source_backed",
            "applicability": {
                "industries": ["all"],
                "countries": ["global"],
                "company_size_bands": ["all"],
                "threats": ["all"],
            },
        }
        manifest = {
            "source_a": {
                "id": "source_a",
                "url": "https://example.com/a",
                "final_url": "https://example.com/a",
                "publication_date": "2026-01-01",
                "status": "fetched",
            },
            "source_b": {
                "id": "source_b",
                "url": "https://example.com/b",
                "final_url": "https://example.com/b",
                "publication_date": "2026-01-02",
                "status": "fetched",
            },
        }

        issues = validate_record_quality(record, manifest)

        self.assertIn(
            "primary_source_id_missing_from_source_ids",
            {issue["code"] for issue in issues},
        )
        self.assertIn("source_id_unknown", {issue["code"] for issue in issues})


if __name__ == "__main__":
    unittest.main()
