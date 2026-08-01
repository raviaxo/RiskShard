import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from engine.sources import (
    content_matches_access_mode,
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
        self.assertIn("first_epss_data_stats", source_ids)
        self.assertIn("asd_annual_cyber_threat_report_2024_2025", source_ids)
        epss = next(
            source for source in registry["sources"]
            if source["id"] == "first_epss_data_stats"
        )
        self.assertFalse(epss["active"])
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

    def test_landing_page_does_not_overwrite_a_declared_pdf_artifact(self):
        """A URL that serves HTML where a PDF was declared must not be accepted.

        The NetDiligence registry entry pointed at a landing page while the manifest held
        a hand-captured 9.1MB PDF. Re-gathering returned HTTP 200 with HTML, which looked
        like success: the manifest recorded a new sha256 and raw_path, silently replacing
        the artifact the evidence cites (found 2026-07-30).
        """
        source = {
            "id": "landing_page_only",
            "title": "Study behind a landing page",
            "publisher": "Example Publisher",
            "source_type": "report",
            "url": "https://example.com/study-landing",
            "publication_date": "2026-01-01",
            "access_mode": "public_pdf",
            "intended_use": ["testing"],
            "usage_notes": "Unit test fixture.",
        }

        def fake_fetch(url, *, timeout):
            return {
                "payload": b"<html>marketing page</html>",
                "final_url": url,
                "http_status": 200,
                "headers": {"Content-Type": "text/html; charset=UTF-8"},
            }

        with TemporaryDirectory() as tmp, patch("engine.sources.fetch_url", side_effect=fake_fetch):
            record = fetch_source(source, Path(tmp), gathered_at="2026-06-01T00:00:00Z", timeout=1, retries=0)
            written = list(Path(tmp).iterdir())

        self.assertEqual(record["status"], "error")
        self.assertIn("landing page", record["error"])
        self.assertIsNone(record["raw_path"])
        # nothing written, so a previously gathered artifact on disk survives
        self.assertEqual(written, [])

    def test_content_mismatch_falls_through_to_a_fallback_url(self):
        """The declared-content guard cooperates with fallback_urls rather than giving up."""
        source = {
            "id": "landing_then_pdf",
            "title": "Study with a working fallback",
            "publisher": "Example Publisher",
            "source_type": "report",
            "url": "https://example.com/landing",
            "fallback_urls": ["https://mirror.example.com/study.pdf"],
            "publication_date": "2026-01-01",
            "access_mode": "public_pdf",
            "intended_use": ["testing"],
            "usage_notes": "Unit test fixture.",
        }

        def fake_fetch(url, *, timeout):
            if url.endswith("/landing"):
                return {
                    "payload": b"<html>marketing page</html>",
                    "final_url": url,
                    "http_status": 200,
                    "headers": {"Content-Type": "text/html"},
                }
            return {
                "payload": b"%PDF-1.7 real study",
                "final_url": url,
                "http_status": 200,
                "headers": {"Content-Type": "application/pdf"},
            }

        with TemporaryDirectory() as tmp, patch("engine.sources.fetch_url", side_effect=fake_fetch):
            record = fetch_source(source, Path(tmp), gathered_at="2026-06-01T00:00:00Z", timeout=1, retries=0)

        self.assertEqual(record["status"], "fetched")
        self.assertEqual(record["final_url"], "https://mirror.example.com/study.pdf")

    def test_mislabelled_pdf_is_accepted_on_its_magic_bytes(self):
        """Some servers send a real PDF with a wrong Content-Type; trust the bytes."""
        self.assertTrue(content_matches_access_mode("public_pdf", "text/html", b"%PDF-1.4 x"))
        self.assertFalse(content_matches_access_mode("public_pdf", "text/html", b"<html>"))
        self.assertTrue(content_matches_access_mode("public_html", "text/html; charset=utf-8"))
        # an unrecognised mode is not policed
        self.assertTrue(content_matches_access_mode("public_api", "application/octet-stream"))

    def test_url_stability_is_validated_and_defaults_to_unassessed(self):
        """A rolling URL serves whatever edition is current, so the artifact drifts away
        from the citation. ibm.com/reports/data-breach did exactly that on 2026-07-31,
        under a record citing the 2025 figure. The field records the property; `unknown`
        is the honest default rather than assuming stability.
        """
        base = {
            "id": "stability_fixture",
            "title": "Fixture",
            "publisher": "Example Publisher",
            "source_type": "report",
            "url": "https://example.com/report-2025",
            "publication_date": "2026-01-01",
            "access_mode": "public_html",
            "intended_use": ["testing"],
            "usage_notes": "Unit test fixture.",
        }
        validate_source(dict(base))  # absent -> defaults, does not raise
        for value in ("dated", "rolling", "unknown"):
            validate_source({**base, "url_stability": value})
        with self.assertRaises(SourceRegistryError):
            validate_source({**base, "url_stability": "probably-fine"})

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
