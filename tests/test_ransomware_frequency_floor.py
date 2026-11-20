"""ADR-0027 — the frequency floor is the published lower bound, band-matched.

`frequency.min` on three shards was **0.10**, described in our own records as a
"global ransomware likelihood floor". The report says:

    "There's about a 10% UPPER BOUND chance that any given organization will
     experience at least one ransomware incident in the next 12 months."

and, on method, that it built "one [estimate] that yields high estimates (upper
bound) and one that gives a lower bound", the upper being "a more risk-averse
view ... generally better suited to managing risk". **Our floor was the
publisher's ceiling**, about twenty times the aggregate lower bound.

How it happened is the part worth keeping. **The publisher's summary page dropped
the qualifier** — it paraphrases the finding as "approximately 10% of
organizations are likely to experience a ransomware incident within the next
year", with no "upper bound" and no mention that a lower bound exists. Our
`extraction_notes` copied that nearly verbatim. The extraction was faithful to
the document it read; it read the wrong document. That is the third finding of
the ADR-0026 campaign and the clearest statement of why it runs.

Table 3 publishes the figure by revenue bracket for both bounds, and all three
org profiles sit in a named bracket above the study's own $10M cutoff.

Every figure here is reader-facing through `docs/EVIDENCE_REPORT.md` and drives a
simulated loss range. This module owns them.
"""
import unittest

import yaml

from engine.project_paths import find_project_root
from engine.tail_bracket import load_evidence_records

ROOT = find_project_root()

SOURCE_ID = "cyentia_iris_ransomware"
SHA = "d2bdaa1d7bf2a20ce8971a1fb4baad432b78d2462938ed55eff5ff0a5def7298"

# Table 3, "One or more" events, read off the held report on 2026-11-20.
TABLE_3 = {
    "$10M to $100M": {"lower": 0.0036, "upper": 0.1132},
    "$100M to $1B": {"lower": 0.0120, "upper": 0.0983},
}
# Figure 8 aggregate, the number the page turned into "approximately 10%".
FIGURE_8_UPPER_AT_LEAST_ONE = 0.0994 + 0.00604 + 0.000267
FIGURE_8_LOWER_AT_LEAST_ONE = 0.00465 + 0.000199 + 0.0000111

SHARDS = {
    "au_finance_ransomware_midmarket": {
        "record": "cyentia_global_ransomware_probability_2025",
        "band": "$10M to $100M",
        "profile": "au_finance_midmarket",
    },
    "de_industrial_ransomware_midmarket": {
        "record": "cyentia_global_ransomware_probability_2025_de_context",
        "band": "$100M to $1B",
        "profile": "de_industrial_midmarket",
    },
    "jp_manufacturing_ransomware_midmarket": {
        "record": "cyentia_global_ransomware_probability_2025_jp_context",
        "band": "$100M to $1B",
        "profile": "jp_manufacturing_midmarket",
    },
}

BRACKET_EDGES = {"$10M to $100M": (10e6, 100e6), "$100M to $1B": (100e6, 1000e6)}


def _records():
    return {r["id"]: r for r in load_evidence_records()}


def _yaml(relpath):
    with open(ROOT / relpath) as handle:
        return yaml.safe_load(handle)


class FrequencyFloorTests(unittest.TestCase):
    def setUp(self):
        self.records = _records()

    def test_each_floor_is_its_bands_published_lower_bound(self):
        for shard, spec in SHARDS.items():
            record = self.records[spec["record"]]
            self.assertEqual(
                record["value"], TABLE_3[spec["band"]]["lower"], (shard, spec["record"])
            )
            self.assertEqual(record["parameter"], "frequency.min", shard)

    def test_the_org_profile_really_sits_in_the_band_we_matched_it_to(self):
        """The band claim is the whole justification. If revenue moves, it breaks.

        An org profile edited across a bracket edge would silently leave its
        shard anchored on the wrong row of Table 3, and nothing else in the
        repository compares the two.
        """
        for shard, spec in SHARDS.items():
            profile = _yaml(f"org_profiles/{spec['profile']}.yaml")
            revenue = profile["annual_revenue_or_budget"]
            low, high = BRACKET_EDGES[spec["band"]]
            self.assertTrue(low <= revenue <= high, (shard, revenue, spec["band"]))
            # The study builds no model below $10M in revenue (footnote 7).
            self.assertGreaterEqual(revenue, 10e6, shard)

    def test_the_scenario_simulates_the_value_the_evidence_carries(self):
        """A scenario and its evidence disagreeing is what the drift check exists for.

        Pinned here too, because the drift check compares a scenario against its
        calibration and this compares it against the record a reader is shown.
        """
        for shard, spec in SHARDS.items():
            scenario = _yaml(f"scenarios/{shard}.yaml")
            self.assertEqual(
                scenario["frequency"]["min"],
                self.records[spec["record"]]["value"],
                shard,
            )

    def test_the_old_value_was_an_upper_bound_and_the_arithmetic_says_so(self):
        """0.10 is the aggregate UPPER bound; the lower one is ~20x smaller.

        If this ever reads differently, the ADR-0027 argument is wrong and the
        re-anchor should be revisited rather than defended.
        """
        self.assertAlmostEqual(FIGURE_8_UPPER_AT_LEAST_ONE, 0.1057, places=4)
        self.assertAlmostEqual(FIGURE_8_LOWER_AT_LEAST_ONE, 0.00486, places=5)
        self.assertGreater(
            FIGURE_8_UPPER_AT_LEAST_ONE / FIGURE_8_LOWER_AT_LEAST_ONE, 20
        )

    def test_every_floor_record_states_both_bounds(self):
        """A floor that hides the publisher's own width is a narrower claim than it looks."""
        for shard, spec in SHARDS.items():
            record = self.records[spec["record"]]
            band = TABLE_3[spec["band"]]
            text = record["limitations"] + " " + record["citation_detail"]
            self.assertIn(f"{band['lower'] * 100:.2f}%", text, shard)
            self.assertIn(f"{band['upper'] * 100:.2f}%", text, shard)

    def test_every_floor_record_records_that_the_page_dropped_the_qualifier(self):
        """The cause, not just the correction — it is why the campaign exists."""
        for shard, spec in SHARDS.items():
            notes = self.records[spec["record"]]["extraction_notes"]
            self.assertIn("upper bound", notes, shard)
            self.assertIn("summary page", notes, shard)

    def test_the_quantity_did_not_change_only_which_estimate_of_it_we_use(self):
        for shard, spec in SHARDS.items():
            self.assertEqual(
                self.records[spec["record"]]["measurement_basis"],
                "org_prevalence_loss_event",
                shard,
            )

    def test_the_four_records_are_recorded_as_read_against_the_held_report(self):
        for spec in SHARDS.values():
            record = self.records[spec["record"]]
            self.assertEqual(record["artifact_verified_sha256"], SHA)
            self.assertEqual(record["artifact_verified_at"], "2026-11-20")
            self.assertEqual(record["source_id"], SOURCE_ID)


class ManufacturingShareTests(unittest.TestCase):
    """The 51% was on the page and in the report from the start, and unrecorded.

    The same sentence gave us the 15% financial-services figure, which *was*
    recorded in 2026-05. Half a sentence was taken and half was left, with two
    manufacturing shards on the board — the eighth time something recorded as
    owed turned out to be already held.
    """

    IDS = (
        "cyentia_manufacturing_ransomware_incident_share_2025",
        "cyentia_manufacturing_ransomware_incident_share_2025_jp_context",
    )

    def setUp(self):
        self.records = _records()

    def test_the_manufacturing_share_is_now_recorded(self):
        for record_id in self.IDS:
            self.assertIn(record_id, self.records, record_id)
            self.assertEqual(self.records[record_id]["value"], 0.51, record_id)

    def test_it_sits_beside_the_financial_services_half_of_the_same_sentence(self):
        fs = self.records["cyentia_fin_services_ransomware_incident_share_2025"]
        self.assertEqual(fs["value"], 0.15)
        self.assertIn("51%", fs["citation_detail"])

    def test_it_cannot_be_mistaken_for_a_frequency(self):
        """A share of incidents is a composition statistic. 51% is not a rate."""
        for record_id in self.IDS:
            record = self.records[record_id]
            self.assertEqual(record["measurement_basis"], "context_statistic")
            self.assertTrue(record["parameter"].startswith("context."), record_id)
            self.assertIn("not an annual probability", record["limitations"], record_id)


if __name__ == "__main__":
    unittest.main()
