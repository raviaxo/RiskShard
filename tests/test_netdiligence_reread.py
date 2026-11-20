"""The five NetDiligence records, read against the report on 2026-11-20.

This group is the counter-example the campaign needed, and it is worth as much
as the findings. **Four of the five verified exactly** — page numbers, figure
numbers, N values and verbatim quotes all matched the publisher file. Someone
had genuinely read the PDF when these were extracted, and two of the records
even say so ("verified in the gathered PDF text").

That matters because it falsifies the lazy reading of ADR-0024: the flagged
population is not 28 bad records. `engine/artifact_fit.py` asks whether a record
cites the report we hold, and these cite the NetDiligence landing page while the
stored artifact is the RSM-hosted PDF. For four of five, that is the *whole*
defect — a citation-URL mismatch, not an unread record.

Two shards' published maxima come from this source
(`ca_finance_data_breach_midmarket` and `us_finance_data_breach_midmarket`,
both `observed_rank`), so a bad read here would have been expensive.

**The fifth had a real problem.** `impact.min` took NetDiligence's USD 152,000
average crisis-services cost, and Figure 11 is titled *"Where Crisis Services
Costs >0"* — the report says plainly that not every claim involves a crisis
services element, which is why its N values vary. So the figure is an average
*conditional on crisis services being incurred*, used as a floor applied to every
modelled event. The value is a defensible construct choice and is unchanged; what
was missing is that the conditioning makes it an overstatement as a floor, and
that the report publishes an observed minimum for the same cell of USD 1,000.
"""
import unittest

from engine.tail_bracket import load_evidence_records

SOURCE_ID = "netdiligence_cyber_claims_2025"
SHA = "4014f4e7a52c55125e3287b2c61ca788f9ae133a8e49408d7e34ec35ba7166cb"
WHEN = "2026-11-20"

VERIFIED_EXACTLY = {
    # record -> (value, the figure read off the report)
    "netdiligence_2025_ca_hacker_claims_average_cost_usd": 66_000,
    "netdiligence_2025_ca_maximum_incident_cost_usd": 15_000_000,
    "us_finance_breach_impact_likely_netdiligence_fs_sme_5yr_usd": 329_000,
    "us_finance_breach_impact_max_netdiligence_fs_sme_observed_usd": 11_500_000,
}
CRISIS = "us_finance_breach_impact_min_netdiligence_sme_crisis_usd"

# Read off the held report, 2026-11-20.
CA_CLAIMS = 84                    # Figure 48, Canada, all revenue sizes
CA_FIVE_YEAR_AVERAGE = 874_000    # "average five-year total incident cost was 874K USD"
FS_CLAIMS = 579                   # Figure 45, Financial Services, SMEs
FS_YEARLY = (201_000, 284_000, 310_000, 517_000, 434_000)
CRISIS_CLAIMS = 4_712             # Figure 11, SMEs, where crisis services costs > 0
FS_OBSERVED_MINIMUM = 1_000       # sector table: cost range starts at $1K


def _records():
    return {r["id"]: r for r in load_evidence_records()}


class NetDiligenceReReadTests(unittest.TestCase):
    def setUp(self):
        self.records = _records()
        for record_id in tuple(VERIFIED_EXACTLY) + (CRISIS,):
            self.assertIn(record_id, self.records, record_id)

    def test_all_five_are_recorded_as_read_against_the_held_report(self):
        for record_id in tuple(VERIFIED_EXACTLY) + (CRISIS,):
            record = self.records[record_id]
            self.assertEqual(record["artifact_verified_at"], WHEN, record_id)
            self.assertEqual(record["artifact_verified_sha256"], SHA, record_id)
            self.assertEqual(record["source_id"], SOURCE_ID, record_id)

    def test_no_value_moved_anywhere_in_this_group(self):
        """Including the crisis-services floor, which is a construct choice and stands."""
        for record_id, value in VERIFIED_EXACTLY.items():
            self.assertEqual(self.records[record_id]["value"], value, record_id)
        self.assertEqual(self.records[CRISIS]["value"], 152_000)

    def test_the_four_sound_records_say_the_flag_was_a_citation_mismatch(self):
        """The distinction the campaign exists to make, written where a reader sees it.

        Without it, a reader of the doctor line reasonably concludes that 28
        records are suspect. Four of these five were never suspect.
        """
        for record_id in VERIFIED_EXACTLY:
            notes = self.records[record_id]["extraction_notes"]
            self.assertIn("citation-URL mismatch", notes, record_id)
            self.assertIn("not an unread record", notes, record_id)

    def test_the_two_published_maxima_still_carry_their_within_sample_exceedance(self):
        """Both are `observed_rank`, and both already say the rank is censored.

        Checked rather than assumed: a re-read that quietly dropped the "true rate
        is higher than 1/N" caveat would make the tail look better understood than
        it is, on two shards' published maxima.
        """
        for record_id, n in (
            ("netdiligence_2025_ca_maximum_incident_cost_usd", CA_CLAIMS),
            ("us_finance_breach_impact_max_netdiligence_fs_sme_observed_usd", FS_CLAIMS),
        ):
            record = self.records[record_id]
            self.assertEqual(record["exceedance_basis"], "observed_rank", record_id)
            self.assertIn(f"N={n}", record["exceedance_detail"], record_id)
            self.assertIn("higher", record["exceedance_detail"], record_id)

    def test_the_bases_the_records_quote_are_the_ones_in_the_report(self):
        self.assertIn(
            f"N={CA_CLAIMS}", self.records["netdiligence_2025_ca_maximum_incident_cost_usd"]["citation_detail"]
        )
        likely = self.records["us_finance_breach_impact_likely_netdiligence_fs_sme_5yr_usd"]
        self.assertIn(f"N={FS_CLAIMS}", likely["citation_detail"])
        for year in FS_YEARLY:
            self.assertIn(f"{year // 1000}K", likely["citation_detail"], year)

    def test_the_five_year_average_is_the_smoothed_figure_not_the_latest_year(self):
        """2023 spiked to 517K and 2024 fell to 434K. The record takes 329K and says why."""
        likely = self.records["us_finance_breach_impact_likely_netdiligence_fs_sme_5yr_usd"]
        self.assertEqual(likely["value"], 329_000)
        self.assertLess(likely["value"], max(FS_YEARLY))
        self.assertIn("five-year average", likely["extraction_notes"])

    def test_the_crisis_floor_now_declares_that_it_is_conditional(self):
        """Figure 11 is "Where Crisis Services Costs >0", so zero-cost claims are excluded.

        A floor derived from an average that excludes the cheap cases overstates
        the floor. The value is unchanged; the omission was the defect.
        """
        record = self.records[CRISIS]
        self.assertIn("Where Crisis Services Costs >0", record["citation_detail"])
        self.assertIn("CONDITIONAL AVERAGE", record["limitations"])
        self.assertIn("overstates", record["limitations"])
        self.assertIn(f"N={CRISIS_CLAIMS:,}", record["limitations"])

    def test_the_crisis_floor_records_the_published_minimum_it_declined(self):
        """USD 1,000 is in the report for this exact cell. Declining it is a choice."""
        notes = self.records[CRISIS]["normalization_notes"]
        self.assertIn(f"USD {FS_OBSERVED_MINIMUM:,}", notes)
        self.assertIn("deliberately not that figure", notes)

    def test_the_crisis_citation_now_names_a_figure(self):
        """It named neither page, figure nor N - the weakest of the five."""
        citation = self.records[CRISIS]["citation_detail"]
        self.assertIn("Figure 11", citation)
        self.assertNotEqual(citation.strip(), "")


if __name__ == "__main__":
    unittest.main()
