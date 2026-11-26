"""The probe is probed, on the defect that bought it.

A tool whose job is to prove guards have teeth cannot be exempt from its own rule, so
these tests build the historical defect as a fixture rather than describing it: a
document carrying a date in a claim **and** a second copy of the same date in a
generated table below it, with two guards over it — one scoped to the claim, one
searching the whole document. Mutating the claim's own copy must make the first fail
and must leave the second passing. If this file ever reports both as caught, the probe
has stopped reproducing the thing it was built for.

The probes here run against fixtures in a temporary directory, never against this
repo's own documents. A suite that mutates `README.md` in place would leave a mutated
file behind on interrupt, and the rule is not worth that.
"""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from engine.mutation import (
    ABSENT, AMBIGUOUS, BASELINE_RED, CAUGHT, HAS_TEETH, SELECTOR_UNRESOLVED,
    TOOTHLESS, UNCAUGHT, format_probe, probe,
)

DOC = """# Fixture

The claim sentence: IBM uses "average" 75 times, read on 2026-08-16.

**The industry** standardised on a shape its evidence base does not produce.

| source | read |
| --- | --- |
| ibm_cost_data_breach_2026 | 2026-08-16 |
"""

FIXTURE_TEST = '''
import unittest
from pathlib import Path

DOC = Path(__file__).resolve().parent / "fixture_doc.md"


def claim_sentence():
    text = DOC.read_text()
    start = text.index("The claim sentence:")
    return text[start:text.index("**The industry", start)]


class Fixture(unittest.TestCase):
    def test_scoped_to_the_claim(self):
        self.assertIn("2026-08-16", claim_sentence())

    def test_whole_document_substring(self):
        self.assertIn("2026-08-16", DOC.read_text())

    def test_always_red(self):
        self.fail("red on purpose")
'''

MUTATE_THE_CLAIM = [
    {"path": "fixture_doc.md", "old": "2026-08-16", "new": "2026-11-12", "occurrence": 1}
]


class MutationProbe(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.doc = self.root / "fixture_doc.md"
        self.doc.write_text(DOC)
        (self.root / "fixture_probe_target.py").write_text(FIXTURE_TEST)
        self.addCleanup(self._tmp.cleanup)

    def sel(self, name):
        return f"fixture_probe_target.Fixture.{name}"

    def test_a_scoped_guard_is_caught_and_reads_as_having_teeth(self):
        report = probe(self.root, self.sel("test_scoped_to_the_claim"), MUTATE_THE_CLAIM)
        self.assertEqual("pass", report["baseline"])
        self.assertEqual(HAS_TEETH, report["verdict"])
        self.assertEqual(CAUGHT, report["mutations"][0]["status"])

    def test_a_document_wide_guard_is_reported_toothless(self):
        """The 2026-11-22 defect, reproduced: the decoy copy in the table keeps it green."""
        report = probe(self.root, self.sel("test_whole_document_substring"), MUTATE_THE_CLAIM)
        self.assertEqual("pass", report["baseline"])
        self.assertEqual(TOOTHLESS, report["verdict"])
        self.assertEqual(UNCAUGHT, report["mutations"][0]["status"])

    def test_mutating_every_occurrence_would_have_hidden_that(self):
        """Why the probe touches one occurrence and refuses to guess which.

        Replacing both copies makes the toothless guard fail, which would have
        reported teeth it does not have. The probe refuses instead.
        """
        both = [{"path": "fixture_doc.md", "old": "2026-08-16", "new": "2026-11-12"}]
        report = probe(self.root, self.sel("test_whole_document_substring"), both)
        entry = report["mutations"][0]
        self.assertEqual(AMBIGUOUS, entry["status"])
        self.assertEqual(2, entry["occurrences"])
        self.assertNotEqual(HAS_TEETH, report["verdict"])

    def test_an_absent_target_is_a_finding_not_a_pass(self):
        gone = [{"path": "fixture_doc.md", "old": "2029-01-01", "new": "2030-01-01"}]
        report = probe(self.root, self.sel("test_scoped_to_the_claim"), gone)
        self.assertEqual(ABSENT, report["mutations"][0]["status"])
        self.assertNotEqual(HAS_TEETH, report["verdict"])

    def test_a_guard_that_is_already_red_teaches_nothing(self):
        report = probe(self.root, self.sel("test_always_red"), MUTATE_THE_CLAIM)
        self.assertEqual(BASELINE_RED, report["verdict"])
        self.assertEqual([], report["mutations"])

    def test_a_mistyped_selector_is_not_reported_as_a_red_guard(self):
        """Found by using the tool, not by reviewing it.

        unittest reports an unloadable selector as a failing test, so the first real
        probe run read BASELINE_RED on a guard that was green — the class name was
        wrong. The two have different fixes and must not share a verdict.
        """
        report = probe(self.root, self.sel("test_no_such_method"), MUTATE_THE_CLAIM)
        self.assertEqual(SELECTOR_UNRESOLVED, report["verdict"])
        self.assertNotEqual(BASELINE_RED, report["verdict"])

    def test_the_target_is_restored_byte_for_byte(self):
        before = self.doc.read_bytes()
        probe(self.root, self.sel("test_scoped_to_the_claim"), MUTATE_THE_CLAIM)
        self.assertEqual(before, self.doc.read_bytes())

    def test_the_target_is_restored_even_when_the_run_raises(self):
        before = self.doc.read_bytes()
        calls = []

        def boom(root, selector, python=None):
            calls.append(selector)
            if len(calls) == 1:
                return True, ""          # baseline green
            raise RuntimeError("the runner fell over mid-mutation")

        with patch("engine.mutation.run_test", boom):
            with self.assertRaises(RuntimeError):
                probe(self.root, self.sel("test_scoped_to_the_claim"), MUTATE_THE_CLAIM)
        self.assertEqual(before, self.doc.read_bytes())

    def test_the_verdict_is_the_first_thing_the_report_says(self):
        report = probe(self.root, self.sel("test_whole_document_substring"), MUTATE_THE_CLAIM)
        rendered = format_probe(report)
        self.assertIn("TOOTHLESS", rendered.splitlines()[1])


if __name__ == "__main__":
    unittest.main()
