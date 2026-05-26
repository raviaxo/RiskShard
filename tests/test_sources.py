import unittest
from pathlib import Path

from engine.sources import (
    SourceRegistryError,
    build_success_record,
    load_source_registry,
    raw_filename_for_source,
    validate_source,
)


ROOT = Path(__file__).resolve().parents[1]


class SourceRegistryTests(unittest.TestCase):
    def test_source_registry_loads_and_validates_required_metadata(self):
        registry = load_source_registry(ROOT / "sources" / "registry.yaml")

        self.assertGreaterEqual(len(registry["sources"]), 5)
        source_ids = {source["id"] for source in registry["sources"]}
        self.assertIn("verizon_dbir_2026", source_ids)
        self.assertIn("cyentia_iris_2025", source_ids)
        self.assertIn("asd_annual_cyber_threat_report_2024_2025", source_ids)

    def test_registry_validation_rejects_missing_publication_date(self):
        source = {
            "id": "bad_source",
            "title": "Bad Source",
            "publisher": "Example",
            "source_type": "report",
            "url": "https://example.com/report.pdf",
            "access_mode": "public_pdf",
            "intended_use": ["testing"],
            "usage_notes": "test",
        }

        with self.assertRaises(SourceRegistryError):
            validate_source(source)

    def test_raw_filename_uses_source_id_and_content_type_extension(self):
        source = {"id": "example_report", "url": "https://example.com/download"}

        self.assertEqual(
            raw_filename_for_source(source, "application/pdf"),
            "example_report.pdf",
        )
        self.assertEqual(
            raw_filename_for_source(source, "text/html; charset=utf-8"),
            "example_report.html",
        )


class SourceManifestTests(unittest.TestCase):
    def test_success_record_includes_audit_hash_and_timestamps(self):
        source = {
            "id": "example_report",
            "title": "Example Report",
            "publisher": "Example Publisher",
            "source_type": "report",
            "url": "https://example.com/report.pdf",
            "publication_date": "2026-01-01",
            "access_mode": "public_pdf",
            "intended_use": ["testing"],
            "usage_notes": "Unit test fixture.",
        }
        payload = b"riskshard source bytes"

        record = build_success_record(
            source,
            gathered_at="2026-05-26T12:00:00Z",
            final_url="https://example.com/report.pdf",
            http_status=200,
            headers={"Content-Type": "application/pdf"},
            payload=payload,
            raw_path=ROOT / "sources" / "raw" / "example_report.pdf",
        )

        self.assertEqual(record["status"], "fetched")
        self.assertEqual(record["publication_date"], "2026-01-01")
        self.assertEqual(record["gathered_at"], "2026-05-26T12:00:00Z")
        self.assertEqual(record["content_length"], len(payload))
        self.assertEqual(
            record["sha256"],
            "969d74567ec925d76077244c8a586b47fd374ece11b6360fd316c6c05409b450",
        )


if __name__ == "__main__":
    unittest.main()
