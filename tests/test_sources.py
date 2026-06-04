import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from engine.sources import (
    SourceRegistryError,
    active_sources,
    build_success_record,
    fetch_source,
    gather_sources,
    load_source_registry,
    raw_filename_for_source,
    source_urls,
    validate_source,
)


ROOT = Path(__file__).resolve().parents[1]


class SourceRegistryTests(unittest.TestCase):
    def test_source_registry_loads_and_validates_required_metadata(self):
        registry = load_source_registry(ROOT / "sources" / "registry.yaml")

        self.assertGreaterEqual(len(registry["sources"]), 5)
        source_ids = {source["id"] for source in registry["sources"]}
        self.assertIn("verizon_dbir_2026", source_ids)
        self.assertIn("ibm_cost_data_breach_2025", source_ids)
        self.assertIn("abs_counts_australian_businesses_2025", source_ids)
        self.assertIn("fbi_ic3_2025_report", source_ids)
        self.assertIn("uk_dsit_cyber_breaches_2026", source_ids)
        self.assertIn("ibm_cost_data_breach_uk_2025", source_ids)
        self.assertIn("fca_equifax_cyber_breach_fine_2023", source_ids)
        self.assertIn("accc_targeting_scams_2025", source_ids)
        self.assertIn("cyentia_iris_2025", source_ids)
        self.assertIn("asd_annual_cyber_threat_report_2024_2025", source_ids)
        asd = next(
            source for source in registry["sources"]
            if source["id"] == "asd_annual_cyber_threat_report_2024_2025"
        )
        self.assertFalse(asd["active"])

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

    def test_fallback_urls_are_attempted_after_primary_url(self):
        source = {
            "id": "example_report",
            "title": "Example Report",
            "publisher": "Example Publisher",
            "source_type": "report",
            "url": "https://example.com/landing",
            "fallback_urls": [
                "https://example.com/report.pdf",
                "https://example.com/report.pdf",
            ],
            "publication_date": "2026-01-01",
            "access_mode": "public_pdf",
            "intended_use": ["testing"],
            "usage_notes": "Unit test fixture.",
        }

        self.assertEqual(
            source_urls(source),
            [
                "https://example.com/landing",
                "https://example.com/report.pdf",
            ],
        )

        calls = []

        def fake_fetch(url, *, timeout):
            calls.append(url)
            if url == "https://example.com/landing":
                raise TimeoutError("landing page timed out")
            return {
                "payload": b"%PDF example",
                "final_url": url,
                "http_status": 200,
                "headers": {"Content-Type": "application/pdf"},
            }

        with TemporaryDirectory() as tmp, patch("engine.sources.fetch_url", side_effect=fake_fetch):
            record = fetch_source(source, Path(tmp), gathered_at="2026-06-01T00:00:00Z", timeout=1, retries=0)

        self.assertEqual(calls, ["https://example.com/landing", "https://example.com/report.pdf"])
        self.assertEqual(record["status"], "fetched")
        self.assertEqual(record["final_url"], "https://example.com/report.pdf")
        self.assertEqual(record["content_type"], "application/pdf")

    def test_gather_sources_skips_inactive_registry_entries(self):
        registry_text = """
sources:
  - id: active_report
    title: Active Report
    publisher: Example
    source_type: report
    url: https://example.com/active.pdf
    publication_date: "2026-01-01"
    access_mode: public_pdf
    intended_use: [testing]
    usage_notes: Active source.
  - id: inactive_report
    title: Inactive Report
    publisher: Example
    source_type: report
    active: false
    url: https://example.com/inactive.pdf
    publication_date: "2026-01-01"
    access_mode: public_pdf
    intended_use: [testing]
    usage_notes: Inactive source.
"""

        def fake_fetch(url, *, timeout):
            return {
                "payload": b"%PDF active",
                "final_url": url,
                "http_status": 200,
                "headers": {"Content-Type": "application/pdf"},
            }

        with TemporaryDirectory() as tmp, patch("engine.sources.fetch_url", side_effect=fake_fetch) as mocked:
            registry_path = Path(tmp) / "registry.yaml"
            registry_path.write_text(registry_text)
            registry = load_source_registry(registry_path)
            manifest = gather_sources(registry_path, Path(tmp) / "raw", retries=0)

        self.assertEqual([source["id"] for source in active_sources(registry)], ["active_report"])
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(manifest["source_count"], 1)
        self.assertEqual(manifest["sources"][0]["id"], "active_report")


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
