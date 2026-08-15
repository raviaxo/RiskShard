"""ADR-0015: the audit must not be able to say more than it has read.

Three findings in this repository have now been the same error in different shapes —
a structured field asserting what the prose beside it denied (finding 5), a stored
value read as intrinsic when it was relative (finding 6), and the one this module
exists to prevent: inferring what a *source publishes* from what *we extracted*.
These tests are the structural guard, not a reminder.
"""
import json
import unittest
from pathlib import Path

import yaml

from engine.source_audit import (
    PROPERTIES,
    VERIFIED,
    audit_coverage,
    audit_defects,
    build_source_audit,
    corpus_view,
    format_audit_markdown,
    load_audit,
    load_registry,
    publishable_claim,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "source_audit_schema.json"


class SchemaTests(unittest.TestCase):
    def test_audit_file_validates(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        data = yaml.safe_load((ROOT / "sources" / "audit.yaml").read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)

    def test_schema_forbids_claiming_what_was_not_read(self):
        """The load-bearing rule, enforced by the schema rather than by review.

        `publishes` is what a reader takes as a statement about the source. An entry
        that carries it on an unread or corpus-derived basis is the conflation
        ADR-0015 exists to prevent, so the schema must reject it outright.
        """
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        def entry(answer):
            return {"audit": [{"source_id": "x", "properties": {
                p: (answer if p == "mode" else {"basis": "unverified"}) for p in PROPERTIES}}]}

        for bad_basis in ("unverified", "derived_from_corpus"):
            with self.assertRaises(jsonschema.ValidationError, msg=bad_basis):
                jsonschema.validate(entry({"basis": bad_basis, "publishes": False}), schema)

        # and a verified answer must say when it was read — an edition can change
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(entry({"basis": VERIFIED, "publishes": False}), schema)

        jsonschema.validate(
            entry({"basis": VERIFIED, "publishes": False, "verified_on": "2026-08-15"}), schema)


class AuditIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.audit = build_source_audit(ROOT)

    def test_no_defects(self):
        self.assertEqual(audit_defects(ROOT), [])

    def test_every_registered_source_is_a_row(self):
        """An unread source is the queue, not an omission.

        Dropping unaudited sources would make coverage look better than it is, which
        is the one number this audit cannot afford to flatter.
        """
        self.assertEqual(len(self.audit["sources"]), len(load_registry(ROOT)))
        audited = {r["source_id"] for r in load_audit(ROOT)}
        rows = {r["source_id"] for r in self.audit["sources"]}
        self.assertTrue(audited <= rows)

    def test_every_verified_answer_names_an_artifact_that_exists(self):
        """A verification nobody can recheck is an assertion."""
        raw = ROOT / "sources" / "raw"
        for row in load_audit(ROOT):
            verified = [p for p in PROPERTIES
                        if (row["properties"].get(p) or {}).get("basis") == VERIFIED]
            if not verified:
                continue
            self.assertTrue(row.get("artifact"), f"{row['source_id']} verified with no artifact")
            self.assertTrue((raw / Path(row["artifact"]).name).exists(),
                            f"{row['source_id']}: {row['artifact']} missing from sources/raw/")

    def test_coverage_counts_every_slot(self):
        c = self.audit["coverage"]
        self.assertEqual(c["slots"], c["sources"] * len(PROPERTIES))
        self.assertEqual(c["verified"] + c["unverified"], c["slots"])

    def test_a_claim_carries_its_denominator(self):
        """`publishable_claim` must not produce a bare statement about the field.

        Finding 1 said "no source consulted does" while resting on two reads. The
        function that replaces that sentence has to report what it did not read.
        """
        for prop in PROPERTIES:
            claim = publishable_claim(self.audit["sources"], prop)
            self.assertEqual(claim["sources_total"], len(self.audit["sources"]))
            self.assertEqual(claim["publishes"] + claim["does_not_publish"],
                             claim["sources_read"])
            self.assertEqual(claim["sources_read"] + claim["unread"], claim["sources_total"])

    def test_corpus_view_is_never_an_answer(self):
        """What we extracted is a fact about us and must not leak into the matrix.

        `corpus_view` is keyed on our own records; if it ever supplied an audit answer
        the audit would be measuring this repository and reporting it as the field.
        """
        corpus = corpus_view(ROOT)
        self.assertTrue(corpus, "expected extraction facts for at least one source")
        for row in self.audit["sources"]:
            for prop in PROPERTIES:
                answer = row["properties"][prop]
                if answer.get("basis") != VERIFIED:
                    self.assertNotIn("publishes", answer,
                                     f"{row['source_id']}/{prop} answers without a read")

    def test_markdown_leads_with_coverage_not_with_findings(self):
        """ADR-0015 part 3: the denominator of our confidence comes first."""
        md = format_audit_markdown(self.audit)
        self.assertIn("Coverage:", md)
        self.assertLess(md.index("Coverage:"), md.index("| Source |"))
        self.assertIn("not a finding", md)

    def test_unread_renders_as_unread(self):
        md = format_audit_markdown(self.audit)
        self.assertIn("is unread. It is not a claim in either direction.", md)


class CoverageMathTests(unittest.TestCase):
    def test_coverage_of_an_empty_audit(self):
        rows = [{"source_id": "a", "properties": {p: {"basis": "unverified"} for p in PROPERTIES}}]
        c = audit_coverage(rows)
        self.assertEqual((c["verified"], c["unverified"], c["sources_fully_verified"]),
                         (0, len(PROPERTIES), 0))

    def test_a_source_counts_as_fully_verified_only_on_all_four(self):
        props = {p: {"basis": VERIFIED, "publishes": False, "verified_on": "2026-08-15"}
                 for p in PROPERTIES}
        props["mode"] = {"basis": "unverified"}
        c = audit_coverage([{"source_id": "a", "properties": props}])
        self.assertEqual(c["verified"], len(PROPERTIES) - 1)
        self.assertEqual(c["sources_fully_verified"], 0)


if __name__ == "__main__":
    unittest.main()
