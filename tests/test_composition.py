"""The composition partition, pinned on evidence we know cold.

`docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md` worked the AU ransomware shard by hand
months before this module existed and published the arithmetic. That makes it the
right thing to check against: if the partition is real it reproduces a number a person
wrote down independently, and if it is fiction it will not.
"""
import unittest

from engine.composition import compose_family, compose_module, classify
from engine.project_paths import find_project_root
from engine.provenance import build_portfolio_provenance
from engine.tail_sensitivity import module_tail_sensitivity

ROOT = find_project_root()
AU = "au_finance_ransomware_midmarket"


class HandCheckedPartitionTests(unittest.TestCase):
    """One shard, checkable on paper: (97,000 + 4*900,000 + 76,000,000) / 6."""

    @classmethod
    def setUpClass(cls):
        cls.composed = compose_module(ROOT, AU)
        cls.impact = cls.composed["families"]["impact"]

    def test_the_mean_is_the_beta_pert_identity(self):
        self.assertAlmostEqual(self.impact["mean"], 79_697_000 / 6, places=6)

    def test_the_maximum_carries_ninety_five_percent_of_the_mean(self):
        """76,000,000 / 79,697,000. The published worked decision says the same thing
        the long way round: a mean of AUD 13.3M against a mode of AUD 900k."""
        shares = {a["slot"]: a["share"] for a in self.impact["anchors"]}
        self.assertAlmostEqual(shares["max"], 76_000_000 / 79_697_000, places=9)
        self.assertAlmostEqual(shares["likely"], 4 * 900_000 / 79_697_000, places=9)
        self.assertAlmostEqual(shares["min"], 97_000 / 79_697_000, places=9)
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=9)
        self.assertAlmostEqual(self.impact["mean"] / 900_000, 14.76, places=2)

    def test_the_partition_runs_on_the_scenario_not_the_evidence_card(self):
        """The calibration converts USD 650,000 to AUD 900,000 before the engine sees
        it. Partitioning the card would break down a figure nobody published."""
        likely = next(a for a in self.impact["anchors"] if a["slot"] == "likely")
        self.assertEqual(likely["value"], 900_000)
        self.assertEqual(likely["evidence_value"], 650_000)

    def test_the_analytic_partition_describes_the_figure_that_gets_published(self):
        """The identity needs no seed and no trials, and this is the proof of it.

        The published annual figure is a seeded Monte Carlo. Under independence its
        expectation is the product of the two family means, which this module computes
        analytically — so agreeing to within simulation noise is what says the shares
        describe the number on the page rather than a parallel calculation of our own.

        Tolerance is 2%: the gap is Monte Carlo error at the configured trial count,
        not a modelling difference, and tightening it would make this test flap.
        """
        simulated = module_tail_sensitivity(ROOT, AU)["base"]["mean"]
        analytic = self.composed["annual_mean"]
        self.assertLess(abs(analytic - simulated) / simulated, 0.02)

    def test_the_per_event_mean_matches_the_tail_module_it_reuses(self):
        """Same identity, two callers. Pinned so they cannot drift apart."""
        self.assertAlmostEqual(self.impact["mean"],
                               module_tail_sensitivity(ROOT, AU)["event_mean"], places=6)

    def test_every_bridge_on_this_shard_is_broader_and_none_is_elsewhere(self):
        """The distinction the label exists to make. Not one anchor was measured on a
        different population; each was measured on one that contains this cell."""
        for anchor in self.impact["anchors"]:
            self.assertEqual(anchor["elsewhere_on"], [], anchor["parameter"])
            self.assertEqual(sorted(anchor["bridged_on"]), sorted(anchor["broader_on"]))

    def test_the_facet_shares_overlap_and_must_not_be_summed(self):
        """One anchor bridged on two facets contributes its whole share to each.

        Pinned because summing them is the obvious mistake and it produces a number
        above 100% that looks like a bug in the data rather than in the reading.
        """
        by_facet = self.impact["bridged_by_facet"]
        self.assertGreater(sum(by_facet.values()), 1.0)
        self.assertLessEqual(max(by_facet.values()), 1.0)


class PartitionShapeTests(unittest.TestCase):
    def test_an_incomplete_family_is_not_partitioned(self):
        """A share of two anchors out of three is a different quantity, same label."""
        self.assertIsNone(compose_family({"min": 1, "likely": 2}, {}, {}, "impact"))
        self.assertIsNone(compose_family(None, {}, {}, "impact"))
        self.assertIsNone(compose_family({"min": 0, "likely": 0, "max": 0}, {}, {}, "impact"))

    def test_a_wildcard_is_bridged_and_a_named_value_is_not(self):
        cell = {"country": "AU", "industry": "financial_services"}
        bridged, broader = classify({"countries": ["all"], "industries": ["financial_services"]}, cell)
        self.assertEqual(bridged, ["country"])
        self.assertEqual(broader, ["country"])
        bridged, broader = classify({"countries": ["US"]}, cell)
        self.assertEqual((bridged, broader), (["country"], []))

    def test_a_facet_the_cell_does_not_set_is_not_tested(self):
        self.assertEqual(classify({"countries": ["US"]}, {}), ([], []))


class PortfolioWeightingTests(unittest.TestCase):
    """Counting parameters and weighting the mean give opposite readings."""

    @classmethod
    def setUpClass(cls):
        from scripts.build_explorer import build_data
        ids = sorted(s["id"] for s in build_data(ROOT)["shards"])
        cls.composed = {i: compose_module(ROOT, i) for i in ids}

    def test_the_answer_is_concentrated_in_one_anchor_in_every_shard(self):
        """No shard's impact mean is evenly spread. "How good is this number?" is
        overwhelmingly "how good is that one anchor?", which a parameter count hides."""
        for module_id, composed in self.composed.items():
            dominant = composed["families"]["impact"]["dominant"]
            self.assertGreater(dominant["share"], 0.5, module_id)

    def test_a_parameter_count_understates_the_shards_that_are_actually_well_anchored(self):
        """The corpus headline is 7 of 66 cell-matched — about 11%. Weighted by how
        much of the answer each anchor carries, three shards are above 85% measured on
        their own cell, because their dominant anchor is the one that matches.

        A count treats `impact.min` at 0.1% of the mean and `impact.max` at 95% as
        equals. If this test fails, the two readings have converged and the argument
        for reporting the weighted share alongside the count needs re-making.
        """
        totals = build_portfolio_provenance(ROOT)["totals"]
        counted = totals["params_cell_matched"] / totals["params_total"]
        weighted = [c["families"]["impact"]["measured_share"] for c in self.composed.values()]
        self.assertLess(counted, 0.2)
        self.assertGreaterEqual(sum(1 for w in weighted if w > 0.85), 3)


if __name__ == "__main__":
    unittest.main()
