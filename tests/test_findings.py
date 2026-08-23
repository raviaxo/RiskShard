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

    def test_every_record_declares_an_applicability(self):
        """Finding 5's first row: the field is required, so the count is the corpus."""
        import yaml

        total = declaring = 0
        for path in sorted((ROOT / "evidence").glob("*.yaml")):
            records = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("records", [])
            for record in records:
                total += 1
                declaring += 1 if record.get("applicability") else 0
        self.assert_row(declaring, total)

    def test_the_repaired_defect_stays_at_zero(self):
        """Finding 5 publishes a repair, so the page must stop being true if it regresses.

        The claim is *0 of 66 cards still claim a bridge their own declaration says
        matches*. `tests/test_provenance.py` fails when that stops holding; this makes
        the published number fail with it rather than quietly outliving the data.
        """
        from engine.provenance import unexplained_bridges

        cards = offenders = 0
        for module in self.provenance["modules"]:
            for card in module["cards"]:
                if not card.get("resolved"):
                    continue
                cards += 1
                offenders += 1 if unexplained_bridges(card, module["cell"]) else 0
        self.assert_row(offenders, cards)
        self.assertEqual(offenders, 0)

    def test_finding_six_counts_match_the_derivation(self):
        """Finding 6: stored fit against the fit derivable from the declaration.

        Unlike finding 5's row, this one is *expected to move* — ADR-0013 decided the
        rendered value becomes the derived one, at which point agreement is 66 of 66
        and this finding becomes a record of what was repaired rather than a live
        defect. The test exists so the page cannot describe the pre-repair state after
        the repair lands.
        """
        from engine.provenance import derivable_bridges

        cards = agree = 0
        for module in self.provenance["modules"]:
            for card in module["cards"]:
                if not card.get("resolved"):
                    continue
                cards += 1
                stored = set(((card.get("population") or {}).get("bridged_on")) or [])
                if stored == set(derivable_bridges(card, module["cell"])):
                    agree += 1
        self.assert_row(agree, cards)
        self.assert_row(cards - agree, cards)

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

    def test_the_front_door_states_the_exceedance_count_correctly(self):
        """The README repeats findings counts, and nothing was checking them.

        It said "7 of 11 impact maxima carry no exceedance" for a day after v0.9.0
        retired two of them. FINDINGS.md was pinned and the front door was not, so the
        page most readers see was the one that drifted.
        """
        import re

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        none_known = 0
        maxima = 0
        for module in self.provenance["modules"]:
            for entry in module_exceedance(module):
                maxima += 1
                none_known += 1 if entry["exceedance_basis"] == "none_known" else 0
        m = re.search(r"\*\*(\d+) of (\d+) impact maxima carry no exceedance", readme)
        self.assertIsNotNone(m, "README no longer states the maxima-without-exceedance count")
        self.assertEqual((int(m.group(1)), int(m.group(2))), (none_known, maxima),
                         "README exceedance count has drifted from the derivation")

    def test_the_front_door_states_the_coherence_count_correctly(self):
        """The maxima count next to it was pinned; this one was not.

        Found 2026-08-22 by scanning every "N of M" in the public docs rather than
        trusting that the ones already pinned were the ones that mattered. The README
        banner was stale in the same sweep, so this is not hypothetical.
        """
        import re

        from engine.coherence import module_coherence

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        coherent = total = 0
        for module in self.provenance["modules"]:
            for family in module_coherence(module):
                total += 1
                coherent += 1 if family["status"] == "coherent" else 0
        m = re.search(r"\*\*(\d+) of (\d+) parameter families are coherent", readme)
        self.assertIsNotNone(m, "README no longer states the coherence count")
        self.assertEqual((int(m.group(1)), int(m.group(2))), (coherent, total),
                         "README coherence count has drifted from the derivation")

    def test_the_front_door_carries_the_source_audit(self):
        """The audit is what the project now leads with publicly (ADR-0016).

        A reader arriving from a post about it must not land on a front door that never
        mentions it. Pins the disclosure and the denominator, not the exact number.
        """
        # collapse wrapping: the README is hard-wrapped and a phrase may straddle lines
        readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("publish a mode", readme)
        self.assertIn("held only as a landing page", readme,
                      "the front door must publish the audit's coverage, not just its result")

    def test_the_front_door_links_to_it(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/FINDINGS.md", readme)
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        self.assertIn("docs/FINDINGS.md", template)


class FindingTenTests(unittest.TestCase):
    """Finding 10's figures, derived rather than trusted.

    This finding exists because a count and a weighting disagree, so its own numbers
    are exactly the kind that go stale silently when an anchor moves.
    """

    @classmethod
    def setUpClass(cls):
        from engine.composition import compose_module
        from scripts.build_explorer import build_data
        cls.text = FINDINGS.read_text(encoding="utf-8")
        ids = sorted(s["id"] for s in build_data(ROOT)["shards"])
        cls.composed = {i: compose_module(ROOT, i) for i in ids}

    def _share(self, module_id, family, key="measured_share"):
        return self.composed[module_id]["families"][family][key]

    def _elsewhere(self, module_id, family):
        anchors = self.composed[module_id]["families"][family]["anchors"]
        return sum(a["share"] for a in anchors if a["elsewhere_on"])

    def test_the_page_states_the_au_anchor_shares(self):
        shares = {a["slot"]: a["share"]
                  for a in self.composed["au_finance_ransomware_midmarket"]["families"]["impact"]["anchors"]}
        for slot, places in (("max", 1), ("likely", 1), ("min", 1)):
            self.assertIn(f"{shares[slot]:.{places}%}", self.text,
                          f"FINDINGS.md no longer states the AU impact.{slot} share")

    def test_the_page_states_the_weighted_shares_it_contrasts(self):
        for module_id, family, kind in (
            ("us_finance_data_breach_midmarket", "impact", "measured"),
            ("sg_finance_bec_midmarket", "impact", "measured"),
            ("us_finance_bec_midmarket", "impact", "measured"),
            ("sg_finance_bec_midmarket", "frequency", "elsewhere"),
            ("fr_finance_data_breach_midmarket", "frequency", "elsewhere"),
        ):
            value = (self._share(module_id, family) if kind == "measured"
                     else self._elsewhere(module_id, family))
            self.assertIn(f"{value:.1%}", self.text,
                          f"FINDINGS.md no longer states {module_id} {family} {kind}={value:.1%}")

    def test_the_finding_holds_no_shard_is_strong_on_both_families(self):
        """The claim itself, not its formatting. A failure means the corpus improved
        and finding 10's second point needs rewriting rather than re-deriving."""
        both = [i for i, c in self.composed.items()
                if c["families"]["frequency"]["measured_share"] > 0.5
                and c["families"]["impact"]["measured_share"] > 0.5]
        self.assertEqual(both, [], f"a shard is now well anchored on both families: {both}")

    def test_the_finding_holds_one_anchor_dominates_every_shard(self):
        for module_id, composed in self.composed.items():
            for family, data in composed["families"].items():
                self.assertGreater(data["dominant"]["share"], 0.5, f"{module_id}.{family}")

    def test_the_page_states_how_many_anchors_were_measured_elsewhere(self):
        elsewhere = sum(1 for c in self.composed.values() for d in c["families"].values()
                        for a in d["anchors"] if a["elsewhere_on"])
        self.assertIn(f"**{elsewhere} are the second kind**", self.text,
                      f"FINDINGS.md no longer states {elsewhere} elsewhere-measured anchors")


if __name__ == "__main__":
    unittest.main()
