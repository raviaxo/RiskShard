"""The published worked decision must keep matching the engine that produced it.

`docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md` states specific figures and reasons from
them in public. If the evidence, the seed derivation or the sampler moves, the document
becomes wrong silently — the same failure class the calibration-drift gate exists to catch.
These pin the figures the argument actually rests on.
"""

import random
import re
import unittest
from pathlib import Path

from engine import fair_calc as fc

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "scenarios/au_finance_ransomware_midmarket.yaml"
DOC = ROOT / "docs" / "WORKED_DECISION_AU_RANSOMWARE_LIMIT.md"
TRIALS = 10000


def _severity(max_anchor=None):
    config = fc.load_and_validate(str(ROOT / SCENARIO))
    seed = fc.derive_scenario_seed(42, SCENARIO, config, root=ROOT)
    impact = config["impact"]
    high = max_anchor if max_anchor is not None else impact["max"]
    rng = random.Random(seed)
    return sorted(
        fc.beta_pert(impact["min"], impact["likely"], high, rng=rng) for _ in range(TRIALS)
    ), impact


class WorkedDecisionFiguresTests(unittest.TestCase):
    def setUp(self):
        self.severity, self.impact = _severity()
        self.text = DOC.read_text(encoding="utf-8")

    def test_per_event_mean_is_far_above_the_mode(self):
        """The claim the whole argument turns on: the mean sits far above the mode.

        Was 14.8x against a mode of AUD 900,000. The 2026 anchor refresh on 2026-08-23
        tripled the mode without moving the maximum, so the ratio nearly halved to 6.16x
        while the claim it supports — that the maximum drives the mean — is untouched.
        The document says both numbers and why they differ.
        """
        mean = sum(self.severity) / TRIALS
        self.assertAlmostEqual(mean, 14_229_567, delta=1)
        self.assertAlmostEqual(mean / self.impact["likely"], 6.16, delta=0.01)

    def test_exceedance_at_the_recommended_limit(self):
        over = [x - 20_000_000 for x in self.severity if x > 20_000_000]
        self.assertAlmostEqual(len(over) / TRIALS, 0.2621, delta=0.0001)
        self.assertAlmostEqual(sum(over) / TRIALS, 2_514_059, delta=1)

    def test_the_max_anchor_alone_swings_the_decision(self):
        """0% to 23% on P(event > 20M) from the max anchor alone."""
        published = sum(1 for x in self.severity if x > 20_000_000) / TRIALS
        cyentia, _ = _severity(44_518_642)
        illustrative, _ = _severity(9_000_000)
        self.assertGreater(published, 0.22)
        self.assertAlmostEqual(sum(1 for x in cyentia if x > 20_000_000) / TRIALS, 0.0742, delta=0.0001)
        self.assertEqual(sum(1 for x in illustrative if x > 20_000_000), 0)

    def test_document_quotes_the_figures_it_reasons_from(self):
        for figure in ("14,229,567", "2,514,059", "26.21%", "76,000,000", "44,518,642"):
            self.assertIn(figure, self.text, f"{figure} missing from the worked decision")

    def test_document_states_what_the_anchors_measure(self):
        """The coherence framing is the point of the document, not decoration."""
        for basis in ("single_documented_event_loss", "cost_component", "mean_total_event_cost"):
            self.assertIn(basis, self.text)

    def test_annualised_and_per_event_are_not_conflated(self):
        config = fc.load_and_validate(str(ROOT / SCENARIO))
        seed = fc.derive_scenario_seed(42, SCENARIO, config, root=ROOT)
        _, annualised = fc.run_simulation(config, TRIALS, "pert", random.Random(seed))
        self.assertAlmostEqual(sum(annualised) / TRIALS, 7_079_188, delta=1)
        # The severity mean must exceed the annualised mean; frequency < 1 scales it down.
        self.assertGreater(sum(self.severity) / TRIALS, sum(annualised) / TRIALS)

    def test_no_currency_conversion_is_invented(self):
        """The USD 32M comparison must use the governed RBA rate, not a guessed one."""
        rates = (ROOT / "calibrations" / "fx_rates.yaml").read_text(encoding="utf-8")
        self.assertIn("0.7188", rates)
        self.assertEqual(round(32_000_000 / 0.7188), 44_518_642)
        self.assertIn("0.7188", self.text)


if __name__ == "__main__":
    unittest.main()
