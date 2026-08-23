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
    """One shard, checkable on paper: (97,000 + 4*2,310,000 + 76,000,000) / 6."""

    @classmethod
    def setUpClass(cls):
        cls.composed = compose_module(ROOT, AU)
        cls.impact = cls.composed["families"]["impact"]

    def test_the_mean_is_the_beta_pert_identity(self):
        self.assertAlmostEqual(self.impact["mean"], 85_337_000 / 6, places=6)

    def test_the_maximum_carries_most_of_the_mean(self):
        """76,000,000 / 85,337,000. The published worked decision says the same thing
        the long way round: a mean of AUD 14.2M against a mode of AUD 2.31M.

        Was 95.4% against a 900,000 mode until the 2026 anchor landed on 2026-08-23.
        The maximum still dominates, by less — which is the disclosure describing its
        own inputs correctly rather than a weakening of the finding.
        """
        shares = {a["slot"]: a["share"] for a in self.impact["anchors"]}
        self.assertAlmostEqual(shares["max"], 76_000_000 / 85_337_000, places=9)
        self.assertAlmostEqual(shares["likely"], 4 * 2_310_000 / 85_337_000, places=9)
        self.assertAlmostEqual(shares["min"], 97_000 / 85_337_000, places=9)
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=9)
        self.assertGreater(shares["max"], 0.85)
        self.assertAlmostEqual(self.impact["mean"] / 2_310_000, 6.157, places=3)

    def test_the_partition_runs_on_the_scenario_not_the_evidence_card(self):
        """The calibration converts USD 1,660,000 to AUD 2,310,000 before the engine
        sees it. Partitioning the card would break down a figure nobody published."""
        likely = next(a for a in self.impact["anchors"] if a["slot"] == "likely")
        self.assertEqual(likely["value"], 2_310_000)
        self.assertEqual(likely["evidence_value"], 1_660_000)

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


class PublishedPayloadTests(unittest.TestCase):
    """The composition has to survive the trip to the page.

    Written because of a mistake made while building this: a claim that the explorer
    had a per-shard disclosure rendering behind a guard that was always false. It did
    not — but it is exactly the failure a payload field can have, silently, forever.
    These tests fail loudly instead.
    """

    @classmethod
    def setUpClass(cls):
        import json
        import re
        from scripts.build_explorer import build_data, render
        cls.shards = build_data(ROOT)["shards"]
        cls.template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        # Rendered here rather than read from docs/index.html, which is generated at
        # deploy time and gitignored: a test that reads it passes only on a machine
        # that has just run the build, and fails on a fresh clone.
        page = render(build_data(ROOT))
        cls.rendered = json.loads(re.search(r'id="rs-data">(.*?)</script>', page, re.S).group(1))

    def test_every_shard_carries_a_complete_composition(self):
        for shard in self.shards:
            families = (shard.get("composition") or {}).get("families") or {}
            self.assertEqual(sorted(families), ["frequency", "impact"], shard["id"])
            for name, data in families.items():
                where = f"{shard['id']}.{name}"
                self.assertAlmostEqual(sum(a["share"] for a in data["anchors"]), 1.0, places=9,
                                       msg=where)
                self.assertAlmostEqual(data["measured_share"] + data["bridged_share"], 1.0,
                                       places=9, msg=where)
                self.assertGreaterEqual(data["elsewhere_share"], 0.0, where)
                self.assertLessEqual(data["elsewhere_share"], data["bridged_share"] + 1e-9, where)

    def test_the_per_shard_cell_matched_count_is_populated_on_every_shard(self):
        """Null on any shard means the page silently says nothing about it."""
        for shard in self.shards:
            self.assertIsNotNone(shard.get("params_cell_matched"), shard["id"])
            self.assertEqual(shard["params_cell_matched"] + shard["params_cross_cell"],
                             len(shard["params"]), shard["id"])

    def test_the_composition_survives_serialisation_into_the_page(self):
        """Guards the build step: the payload is embedded as JSON in the page, and a
        field that does not serialise is a field the reader never sees."""
        rendered = {s["id"]: s for s in self.rendered["shards"]}
        self.assertEqual(sorted(rendered), sorted(s["id"] for s in self.shards))
        for shard in self.shards:
            live = shard["composition"]["families"]["impact"]["measured_share"]
            page = (rendered[shard["id"]].get("composition") or {}).get("families", {})
            self.assertIn("impact", page, f"{shard['id']} has no composition on the page")
            self.assertAlmostEqual(page["impact"]["measured_share"], live, places=9,
                                   msg=shard["id"])

    def test_the_template_still_renders_the_composition(self):
        """A payload nothing reads is not a disclosure."""
        self.assertIn("compositionNote(s)", self.template)
        self.assertIn("s.composition", self.template)
        self.assertIn("What this figure rests on", self.template)


class ExecutiveReportDisclosureTests(unittest.TestCase):
    """The board-facing surface, where the omission was worst.

    "How much to trust it" said `N of M model parameters are backed by public sources`
    and nothing else. For every shard in this portfolio that reads 6 of 6, which a
    board reads as a completeness score — while for eight of eleven shards **none** of
    those sources measured the population being asked about.
    """

    @classmethod
    def setUpClass(cls):
        from engine.executive_report import build_executive_report, format_executive_report_markdown
        from engine.risk_modules import find_risk_module
        run = {"portfolio": {"mean": 1.0, "p50": 1.0, "p95": 2.0, "p99": 3.0},
               "metadata": {"trials": 10, "distribution": "pert"}}
        module = find_risk_module("us_finance_data_breach_midmarket", ROOT)
        cls.report = build_executive_report(run, module=module, pack={}, root=ROOT)
        cls.markdown = format_executive_report_markdown(cls.report)

    def test_the_report_states_what_the_figure_rests_on(self):
        self.assertIn("What the figure rests on", self.markdown)
        self.assertIn("Frequency", self.markdown)
        self.assertIn("Impact", self.markdown)

    def test_it_distinguishes_measured_elsewhere_from_merely_broader(self):
        """This shard is the reason the distinction is not academic: its impact side is
        99% measured on its own cell and its frequency side is 100% measured on another
        country. One number for both would be false of one of them."""
        self.assertIn("measured on a different one", self.markdown)

    def test_it_says_what_backed_by_public_sources_does_not(self):
        self.assertIn("says the evidence is published; this says who it was measured on",
                      self.markdown)

    def test_the_disclosure_sits_with_the_trust_claim_it_qualifies(self):
        """Not in a footnote. A caveat a board reaches after the decision section is a
        caveat that did not happen."""
        trust = self.markdown.index("## How much to trust it")
        rests = self.markdown.index("What the figure rests on")
        decision = self.markdown.index("## Decision the board is being asked to support")
        self.assertLess(trust, rests)
        self.assertLess(rests, decision)

    def test_an_uncomputable_composition_says_so_rather_than_vanishing(self):
        """The failure mode this whole line of work exists to fix: a disclosure that
        degrades to silence leaves the page reading as complete."""
        from engine.executive_report import _composition_lines
        text = "\n".join(_composition_lines({"composition": None}))
        self.assertIn("could not be computed", text)
        self.assertIn("Do not read its absence as nothing to state", text)

    def test_a_report_without_a_root_still_builds(self):
        """The composition is an addition, not a new requirement."""
        from engine.executive_report import build_executive_report
        run = {"portfolio": {"mean": 1, "p50": 1, "p95": 2, "p99": 3},
               "metadata": {"trials": 10, "distribution": "pert"}}
        report = build_executive_report(run, module={}, pack={})
        self.assertIsNone(report["composition"])


if __name__ == "__main__":
    unittest.main()
