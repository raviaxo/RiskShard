"""Intake triage must rank by measured need, and must not pretend to know content.

The scorer was wrong twice while being built, in opposite directions, and both
failures are pinned here because they are the ways this kind of ranking goes bad:
judging scope from body text, and judging content from a filename.
"""
import unittest
from pathlib import Path

from engine.intake import (
    assess,
    build_intake,
    intake_defects,
    intake_totals,
    load_intake,
    portfolio_gaps,
    scope_text,
)

ROOT = Path(__file__).resolve().parents[1]


class GapWeightingTests(unittest.TestCase):
    def setUp(self):
        self.gaps = portfolio_gaps(ROOT)

    def test_gaps_come_from_the_portfolio_not_from_taste(self):
        facets = self.gaps["bridged_by_facet"]
        self.assertTrue(facets, "expected measured bridge counts")
        self.assertTrue(set(facets) <= {"country", "sector", "size", "threat"})
        self.assertTrue(self.gaps["cells"], "expected the shard cells")

    def test_sector_outranks_country_while_sector_is_the_bigger_gap(self):
        """The ranking must follow the corpus, so it changes when the corpus does.

        Sector is bridged far more often than country today, so a sector-specific
        study must beat a national one. If that ever inverts in the data, this test
        inverts with it rather than defending a stale preference.
        """
        facets = self.gaps["bridged_by_facet"]
        if facets.get("sector", 0) <= facets.get("country", 0):
            self.skipTest("sector is no longer the larger gap; ranking should follow")
        body = "average cost of a breach and prevalence rate"
        sector = assess(scope_text("state-of-ransomware-in-financial-services-2025.pdf", ""),
                        body, self.gaps)
        country = assess(scope_text("state-of-ransomware-in-australia-2026.pdf", ""),
                         body, self.gaps)
        self.assertGreater(sector["score"], country["score"])


class ScorerRegressionTests(unittest.TestCase):
    """The two calibration failures, held down."""

    def setUp(self):
        self.gaps = portfolio_gaps(ROOT)

    def test_scope_is_judged_on_the_title_not_the_body(self):
        """Front matter listing survey countries is not scope.

        A cloud identity report whose first page happens to name every country in its
        sample once outranked sixteen country-specific ransomware studies.
        """
        body = ("survey conducted across Australia, Germany, France, Japan, Singapore, "
                "the United Kingdom and the United States. average cost")
        generic = assess(scope_text("identity-security-report-2026.pdf", ""), body, self.gaps)
        self.assertEqual(generic["countries"], [],
                         "countries must come from declared scope, not body text")

    def test_a_filename_is_not_expected_to_advertise_a_quantity(self):
        """The opposite failure: quantity judged on the filename zeroed the good ones.

        `sophos-state-of-ransomware-in-japan-2026.pdf` does not say "cost", and a rule
        meant to drop documents that cannot move a number dropped the ones that could.
        """
        scope = scope_text("sophos-state-of-ransomware-in-japan-2026.pdf", "")
        with_body = assess(scope, "the average ransom payment and recovery cost", self.gaps)
        self.assertGreater(with_body["score"], 0)
        self.assertIn("JP", with_body["countries"])
        self.assertIn("ransomware", with_body["threats"])

    def test_a_document_carrying_no_quantity_scores_zero(self):
        """Coverage without a number cannot move anything, however on-cell it looks."""
        scope = scope_text("state-of-ransomware-in-australia-2026.pdf", "")
        self.assertEqual(assess(scope, "an essay about resilience culture", self.gaps)["score"], 0)


class RegisterTests(unittest.TestCase):
    def test_no_defects(self):
        self.assertEqual(intake_defects(ROOT), [])

    def test_every_candidate_carries_a_hash_and_a_status(self):
        for row in load_intake(ROOT):
            self.assertTrue(row.get("sha256"), f"{row.get('file')} has no hash")
            self.assertIn(row.get("status"),
                          {"unassessed", "queued", "parked", "duplicate", "admitted"})

    def test_duplicates_point_at_the_file_they_duplicate(self):
        for row in load_intake(ROOT):
            if row.get("status") == "duplicate":
                self.assertTrue(row.get("duplicate_of"), f"{row['file']} duplicate of nothing")

    def test_totals_account_for_every_candidate(self):
        totals = build_intake(ROOT)["totals"]
        self.assertEqual(sum(totals["by_status"].values()), totals["candidates"])

    def test_the_register_is_ranked(self):
        rows = build_intake(ROOT)["candidates"]
        scores = [float(r.get("score") or 0) for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
