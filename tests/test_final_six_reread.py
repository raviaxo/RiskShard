"""The last six records of the ADR-0026 campaign, read 2026-11-20.

With these the flagged population reads **28 re-read, 0 not yet** — the first
time the campaign's own counter has shown a finished job rather than a backlog.

Three sources, three different kinds of outcome:

**Cyentia IRIS 2022 — the label named the wrong statistic.** `$266K` is the
**geometric mean**; the median is `$259K`, and Table 3 prints both. Three records
carried `median_total_event_cost`. [ADR-0028](../docs/adr/0028-a-geometric-mean-is-its-own-basis.md)
mints `geometric_mean_total_event_cost` rather than swapping the value to fit the
dictionary. The same table shows why folding a geomean into "mean" would have been
worse than the original error: the arithmetic mean of this distribution is over
**$25M**, about a hundred times the geomean, and the report says so itself.

**Ponemon/DTEX 2023 — two categories spliced together.** The malicious-insider
record read *"an average of 6.2 incidents and an average cost per incident of
$701,500"*. The cost is right. **6.2 is the credential-theft frequency**; criminal
and malicious insider incidents average **6.9** (Figure 2). Both numbers are in
the report, on different profiles. No check caught it, and it stopped mattering
only because the 2026 edition superseded the record and read Table 2 correctly —
an edition refresh is not a review.

**IBM 2025 — exact, from a paraphrase.** `USD 4.44M` matches the report's own
sentence. The citation had quoted a secondary paraphrase rather than the report.
"""
import unittest

from engine.slot_roles import CENTRAL_TENDENCY_BASES
from engine.tail_bracket import load_evidence_records

SHA = {
    "iris2022": "8cf45ef222a4375dba486bd942c5734796e65b93f181e3431e60efed0d491677",
    "ponemon": "1103b630847fa8f308c79033521d8182eeb79f3836aa29fec3c501527d8ebe25",
    "ibm": "e60c77ff14afe3d9d0f72dd5b2845329568735cc41567f45aaaf715b7952e910",
}

IRIS_2022 = (
    "cyentia_iris_2022_typical_cyber_event_loss_usd",
    "cyentia_iris_2022_typical_cyber_event_loss_usd_de_industrial_context",
    "cyentia_iris_2022_typical_cyber_event_loss_usd_jp_manufacturing_context",
)
MALICIOUS = "ponemon_2023_malicious_insider_per_incident_usd"
CREDENTIAL = "ponemon_2023_insider_credential_theft_per_incident_usd"
IBM_RECORD = "ibm_cost_data_breach_2025_global_average_cost_usd_ca_context"

# IRIS 2022 Table 3, N=1,893 events. Read off the held report.
GEOMEAN = 266_000
MEDIAN = 259_000
ARITHMETIC_MEAN_FLOOR = 25_000_000   # the report: "over $25M"
EVENTS = 1_893

# Ponemon 2023 Figure 2, average incidents per organization.
CREDENTIAL_THEFT_INCIDENTS = 6.2     # what the record wrongly attributed
MALICIOUS_INSIDER_INCIDENTS = 6.9    # the real figure for that profile
NEGLIGENT_AVERAGE = 505_113          # the commonest profile, and cheaper than our floor


def _records():
    return {r["id"]: r for r in load_evidence_records()}


class CampaignCompleteTests(unittest.TestCase):
    def test_every_flagged_record_has_now_been_read(self):
        """The counter ADR-0026 existed to make movable, at the end of its range.

        If this fails because the total grew, that is ordinary evidence work
        adding a record that cites a page — read it and the count returns to
        zero. If it fails because something went *stale*, a publisher reissued a
        file and the record needs re-reading. The two are distinguishable by the
        stale count, which is why both are asserted.
        """
        from engine.artifact_fit import fit_report

        totals = fit_report()["totals"]
        self.assertEqual(totals["flagged_unverified"], 0)
        self.assertEqual(totals["flagged_stale"], 0)
        self.assertEqual(
            totals["flagged_verified"], totals["cites_a_page_for_a_report_we_hold"]
        )


class Iris2022Tests(unittest.TestCase):
    def setUp(self):
        self.records = _records()

    def test_the_basis_now_names_the_statistic(self):
        for record_id in IRIS_2022:
            record = self.records[record_id]
            self.assertEqual(
                record["measurement_basis"], "geometric_mean_total_event_cost", record_id
            )
            self.assertEqual(record["value"], GEOMEAN, record_id)

    def test_a_geometric_mean_is_still_a_central_tendency(self):
        """Omitting it from this set would have retired a finding by renaming it.

        All three records sit in `min` slots. `slot_roles` flags a central
        tendency used as a minimum, and that flag is published as finding 1. A
        new basis outside `CENTRAL_TENDENCY_BASES` would have silently cleared
        three of its rows.
        """
        self.assertIn("geometric_mean_total_event_cost", CENTRAL_TENDENCY_BASES)

    def test_the_median_it_is_not_is_recorded_beside_it(self):
        for record_id in IRIS_2022:
            text = self.records[record_id]["citation_detail"] + self.records[record_id]["limitations"]
            self.assertIn(f"{MEDIAN:,}", text, record_id)
            self.assertIn(f"N={EVENTS:,}", text, record_id)

    def test_the_reason_a_geomean_is_not_a_mean_is_on_the_record(self):
        """$266K against an arithmetic mean over $25M — about 100x apart."""
        self.assertGreater(ARITHMETIC_MEAN_FLOOR / GEOMEAN, 90)
        for record_id in IRIS_2022:
            self.assertIn("25,000,000", self.records[record_id]["limitations"], record_id)

    def test_all_three_are_recorded_as_read_against_the_held_report(self):
        for record_id in IRIS_2022:
            self.assertEqual(self.records[record_id]["artifact_verified_sha256"], SHA["iris2022"])


class PonemonTests(unittest.TestCase):
    def setUp(self):
        self.records = _records()

    def test_the_spliced_frequency_is_gone_from_the_citation(self):
        record = self.records[MALICIOUS]
        self.assertNotIn("6.2", record["citation_detail"])
        self.assertIn("701,500", record["citation_detail"])
        self.assertIn("1,874", record["citation_detail"])

    def test_both_frequencies_are_recorded_with_the_profile_each_belongs_to(self):
        notes = self.records[MALICIOUS]["extraction_notes"]
        self.assertIn(str(CREDENTIAL_THEFT_INCIDENTS), notes)
        self.assertIn(str(MALICIOUS_INSIDER_INCIDENTS), notes)
        self.assertIn("CREDENTIAL THEFT", notes)

    def test_the_lesson_that_an_edition_refresh_is_not_a_review_is_recorded(self):
        """It stopped mattering by accident. That is worth keeping, not burying."""
        self.assertIn(
            "edition refresh is not a review", self.records[MALICIOUS]["limitations"]
        )

    def test_the_selected_floor_names_the_cheaper_published_profile(self):
        """"Can cost far less" was hypothetical. The report publishes the number.

        Negligent or mistaken insiders are the *most frequent* profile at 55% of
        incidents, and average USD 505,113 — below the floor this record sets.
        """
        record = self.records[CREDENTIAL]
        self.assertEqual(record["value"], 679_621)
        self.assertIn(f"{NEGLIGENT_AVERAGE:,}", record["limitations"])
        self.assertLess(NEGLIGENT_AVERAGE, record["value"])
        self.assertIn("BELOW this floor", record["limitations"])


class IbmTests(unittest.TestCase):
    def test_the_citation_quotes_the_report_not_a_paraphrase(self):
        record = _records()[IBM_RECORD]
        self.assertEqual(record["value"], 4_440_000)
        self.assertIn("4.44 million", record["citation_detail"])
        self.assertIn("4.88 million", record["citation_detail"])
        self.assertEqual(record["artifact_verified_sha256"], SHA["ibm"])


if __name__ == "__main__":
    unittest.main()
