"""The join between what the audit cannot read and what is already on disk.

Seven times a source recorded as owed turned out to be held. The last one was the
sharpest: the real *Cost of Insider Risks Global Report 2023* sat in the intake
register marked `parked` while the audit row for that exact source read
`no_readable_artifact`, because the gatherer had only ever reached its announcement
page. Both records were correct in isolation.
"""
import unittest

from engine.intake import _title_tokens, blocked_but_held
from engine.project_paths import find_project_root

ROOT = find_project_root()


class TitleMatchingTests(unittest.TestCase):
    def test_the_year_is_significant(self):
        """Dropping it made every Sophos country cut match every other year of
        itself, which turns a useful check into noise nobody reads."""
        au25 = _title_tokens("The State of Ransomware in Australia 2025 (whitepaper)")
        au26 = _title_tokens("THE STATE OF RANSOMWARE IN AUSTRALIA 2026 Findings from a survey")
        self.assertFalse(au25 <= au26)
        self.assertFalse(au26 <= au25)

    def test_packaging_words_do_not_decide_a_match(self):
        source = _title_tokens("Cost of Insider Risks Global Report 2023")
        candidate = _title_tokens(
            "Cost of Insider Risks GLOBAL REPORT 2023 Independently conducted by Table of contents")
        self.assertTrue(source <= candidate)

    def test_a_different_document_does_not_match(self):
        source = _title_tokens("Cost of Insider Risks Global Report 2023")
        other = _title_tokens("2026 Data Breach Investigations Report")
        self.assertFalse(source <= other)


class BlockedButHeldTests(unittest.TestCase):
    def test_the_live_corpus_has_none(self):
        """The regression guard. A failure means a document is on disk for a source
        the audit says it cannot read — which is the exact state this check exists
        to stop recurring, and it is now the doctor's job to fail on it.
        """
        held = blocked_but_held(ROOT)
        self.assertEqual(held, [], f"blocked sources with a held document: {held}")

    def test_the_matcher_finds_the_case_it_was_built_for(self):
        """Proved on synthetic records rather than on the corpus, because the real
        case has been fixed — and a check verified only by the absence of a hit is
        indistinguishable from a check that does nothing.
        """
        from engine.source_audit import NO_ARTIFACT

        registry = [{"id": "acme_insider_2023", "title": "Cost of Insider Risks Global Report 2023"}]
        audit = [{"source_id": "acme_insider_2023",
                  "properties": {p: {"basis": NO_ARTIFACT} for p in
                                 ("mode", "distribution", "exceedance", "population")}}]
        intake = [{"file": "downloaded_name.pdf", "words": 9852, "status": "parked",
                   "title": "Cost of Insider Risks GLOBAL REPORT 2023 Independently conducted by"}]

        import engine.intake as module
        import engine.source_audit as audit_module
        originals = (module.load_intake, audit_module.load_audit, audit_module.load_registry)
        try:
            module.load_intake = lambda _root: intake
            audit_module.load_audit = lambda _root: audit
            audit_module.load_registry = lambda _root: registry
            found = blocked_but_held(ROOT)
        finally:
            module.load_intake, audit_module.load_audit, audit_module.load_registry = originals

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["source_id"], "acme_insider_2023")
        self.assertEqual(found[0]["file"], "downloaded_name.pdf")


if __name__ == "__main__":
    unittest.main()
