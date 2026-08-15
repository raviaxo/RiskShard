"""docs/FINDINGS.md publishes counts about this repository. They must still be true.

The page is the project's most load-bearing public claim — it says what we got wrong —
so a stale number on it is worse than a stale number anywhere else. Every headline count
is re-derived here from the same tool that produced it and asserted against the published
text, so the page cannot drift away from the repository it describes.

The precedent is the 7-vs-8 recount (2026-08-12): a hand-carried count was wrong by one
shard for as long as nothing checked it.
"""
import re
import unittest
from pathlib import Path

from engine.coherence import build_portfolio_coherence
from engine.exceedance import module_exceedance
from engine.provenance import build_portfolio_provenance
from engine.slot_roles import build_portfolio_slot_roles

ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "docs" / "FINDINGS.md"


class FindingsPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = FINDINGS.read_text(encoding="utf-8")
        cls.provenance = build_portfolio_provenance(ROOT)

    def assert_row(self, count, total):
        """The page states counts as `**N of M**` inside its tables."""
        self.assertIn(
            f"**{count} of {total}**", self.text,
            f"FINDINGS.md no longer states '{count} of {total}' — re-derive the page",
        )

    def test_slot_role_counts_match_the_derivation(self):
        totals = build_portfolio_slot_roles(ROOT)["totals"]
        shards = totals["shards"]
        self.assert_row(0, shards)                                          # modes: none
        self.assert_row(totals["shards_mode_slot_central_tendency"], shards)
        self.assert_row(totals["shards_floor_slot"], shards)

    def test_coherence_counts_match_the_derivation(self):
        totals = build_portfolio_coherence(ROOT)["totals"]
        self.assert_row(totals["coherent"], totals["families"])
        self.assert_row(totals["mixed"], totals["families"])
        self.assert_row(totals["shards_with_a_mixed_family"], totals["shards"])

    def test_exceedance_counts_match_the_derivation(self):
        maxima = quantified = none_known = 0
        for module in self.provenance["modules"]:
            for entry in module_exceedance(module):
                maxima += 1
                quantified += 1 if entry["quantified"] else 0
                none_known += 1 if entry["exceedance_basis"] == "none_known" else 0
        self.assert_row(quantified, maxima)
        self.assert_row(none_known, maxima)

    def test_population_counts_match_the_derivation(self):
        t = self.provenance["totals"]
        self.assert_row(t["params_source_backed"], t["params_total"])
        self.assert_row(t["params_cell_matched"], t["params_total"])
        self.assert_row(t["params_cross_cell"], t["params_total"])

    def test_declared_applicability_counts_match_the_derivation(self):
        """Finding 5: `applicability` is a declaration, not the measured population.

        Derived from the evidence files rather than from a card, because the claim is
        about what the records themselves say — a record contradicts its own
        `population_match` when it declares a narrow value on a facet that field says
        the source did not measure.
        """
        import yaml

        facets = {"sector": "industries", "size": "company_size_bands",
                  "country": "countries", "threat": "threats"}
        total = declaring = contradicting = 0
        for path in sorted((ROOT / "evidence").glob("*.yaml")):
            records = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("records", [])
            for record in records:
                total += 1
                declared = record.get("applicability") or {}
                declaring += 1 if declared else 0
                bridged_on = (record.get("population_match") or {}).get("bridged_on") or []
                narrow = [
                    dim for dim in bridged_on
                    if (declared.get(facets[dim]) or [])
                    and not {"all", "global"} & set(declared.get(facets[dim]) or [])
                ]
                contradicting += 1 if narrow else 0
        self.assert_row(declaring, total)
        self.assert_row(contradicting, total)
        # No record states the observed population, and the page says so as a count.
        self.assert_row(0, total)

    def test_the_bridged_split_matches_the_derivation(self):
        """Finding 5: how much of the `bridged` flag is actually about our target.

        The merged flag is two unlike things, so the page publishes the split. If a
        future change moves either side, this fails rather than letting the page claim
        a decomposition the code no longer produces.
        """
        from engine.provenance import cell_mismatch

        bridged = target_relative = 0
        for module in self.provenance["modules"]:
            for card in module["cards"]:
                if (card.get("population") or {}).get("status") != "bridged":
                    continue
                bridged += 1
                target_relative += 1 if cell_mismatch(card) else 0
        self.assert_row(bridged, self.provenance["totals"]["params_total"])
        self.assert_row(bridged - target_relative, bridged)
        self.assert_row(target_relative, bridged)

    def test_the_page_records_what_the_project_got_wrong(self):
        """Corrections are the point of the page, not an appendix to it."""
        for marker in ("Retracted figures", "Withdrawn claim 1", "Withdrawn claim 2",
                       "Framings retired"):
            self.assertIn(marker, self.text)

    def test_retraction_count_matches_the_correction_log(self):
        recorded = 0
        for path in (ROOT / "revisions").glob("*.yaml"):
            match = re.search(r"^retractions:\s*(\d+)", path.read_text(encoding="utf-8"), re.M)
            if match:
                recorded += int(match.group(1))
        self.assertIn(
            f"Retracted figures — {recorded} ", self.text,
            f"the correction log records {recorded} retracted figures",
        )

    def test_direction_of_error_language_appears_only_where_it_is_withdrawn(self):
        """Withdrawn claim 1 exists because this language was used once and was wrong.

        The page has to quote it to withdraw it, so the rule is placement, not absence:
        no direction-of-error phrasing may appear in the findings themselves.
        """
        self.assertIn("has no referent", self.text)
        corrections = self.text.index("## What we got wrong")
        for phrase in ("overstating loss", "inflates the published", "too high relative"):
            position = self.text.find(phrase)
            if position != -1:
                self.assertGreater(
                    position, corrections,
                    f"'{phrase}' appears in a finding rather than in its withdrawal",
                )

    def test_the_front_door_links_to_it(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/FINDINGS.md", readme)
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        self.assertIn("docs/FINDINGS.md", template)


if __name__ == "__main__":
    unittest.main()
