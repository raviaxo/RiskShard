"""The six IRIS 2025 records, read against the report on 2026-11-20.

This is the source [ADR-0024](../docs/adr/0024-the-published-bracket.md) is named
for, and the re-read is the cleanest available demonstration of its thesis —
because **the publisher's summary page is not wrong.** It says, accurately:

    "Median losses from security incidents have increased 15x, rising from $190K
     to nearly $3M, with extreme events reaching $32M."

All six records quote that faithfully. It is 4,111 characters, and extracting
from it instead of the report cost two things that are in the report in plain
sight:

1. **$32M is the 95th percentile.** Figure 9 is labelled `$32M (95%)` and the
   body text says *"more extreme (95th percentile) losses swell to $32 million"*.
   Three records carried `exceedance_basis: none_known` and a caveat saying the
   figure was "not a formal percentile for this scenario", which reads as no
   percentile existing. It exists, and it is stated twice.

2. **The $3M is not the distribution's median.** The report holds two medians:
   Figure 9's pooled 2015-2024 median of **$603K**, and Figure 10's trend, whose
   2024 endpoint is **$2.9M** after a 15.20x rise from $189.9K. The $3M we store
   is the trend endpoint — a single-year median sitting ~4.8x above the pooled
   one — and nothing on the record said so. `impact.likely` for the
   third-party-outage drift-watch scenario is this record, on a calibration whose
   own notes say its impact side rests entirely on these Cyentia bridges.

The page also puts the $32M beside a "5-fold rise" belonging to the **90th**
percentile ($6.0M -> $28.5M). Both statistics are real and they are not the same
one; the records now say so, so nobody later "reconciles" $32M against $28.5M.

Every figure above is reader-facing through `docs/EVIDENCE_REPORT.md`. This
module owns them.
"""
import unittest

from engine.project_paths import find_project_root
from engine.tail_bracket import build_portfolio_brackets, load_evidence_records

ROOT = find_project_root()

SOURCE_ID = "cyentia_iris_2025"
# sha256 of sources/raw/cyentia_iris_2025.pdf, matching sources/manifest.json.
SHA = "00706bbbfefcc7b6cc321dcbcc2347b3082af92572cbd55abd2239a901cf8f1c"
WHEN = "2026-11-20"

EXTREMES = (
    "cyentia_iris_2025_extreme_security_incident_loss_usd",
    "cyentia_iris_2025_extreme_security_incident_loss_usd_de_industrial_context",
    "cyentia_iris_2025_extreme_security_incident_loss_usd_jp_manufacturing_context",
)
MEDIANS = (
    "cyentia_iris_2025_median_security_incident_loss_usd_de_industrial_context",
    "cyentia_iris_2025_median_security_incident_loss_usd_jp_manufacturing_context",
    "cyentia_iris_2025_median_security_incident_loss_usd_third_party_outage_context",
)

# Read off the held report, 2026-11-20.
FIGURE_9_MEDIAN = 603_000          # pooled 2015-2024 median
FIGURE_9_P95 = 32_000_000          # pooled 2015-2024 95th percentile
FIGURE_10_MEDIAN_2008 = 189_900
FIGURE_10_MEDIAN_2024 = 2_900_000  # the figure our $3M rounds from
FIGURE_10_P90_2024 = 28_500_000    # NOT the $32M, and the reason to say so


def _records():
    return {r["id"]: r for r in load_evidence_records()}


class IrisReReadTests(unittest.TestCase):
    def setUp(self):
        self.records = _records()
        for record_id in EXTREMES + MEDIANS:
            self.assertIn(record_id, self.records, record_id)

    def test_all_six_are_recorded_as_read_against_the_held_report(self):
        for record_id in EXTREMES + MEDIANS:
            record = self.records[record_id]
            self.assertEqual(record["artifact_verified_at"], WHEN, record_id)
            self.assertEqual(record["artifact_verified_sha256"], SHA, record_id)
            self.assertEqual(record["source_id"], SOURCE_ID, record_id)

    def test_no_value_moved(self):
        """A re-read that moved a value would need its own approval, not this one."""
        for record_id in EXTREMES:
            self.assertEqual(self.records[record_id]["value"], FIGURE_9_P95, record_id)
        for record_id in MEDIANS:
            self.assertEqual(self.records[record_id]["value"], 3_000_000, record_id)

    def test_the_published_percentile_is_no_longer_declared_missing(self):
        """The ADR-0024 defect, corrected at the record level.

        `none_known` means "no exceedance statement is available" (ADR-0008).
        One was available, printed twice, in a report we hold and had verified.
        """
        for record_id in EXTREMES:
            record = self.records[record_id]
            self.assertEqual(record["exceedance_basis"], "modeled_quantile", record_id)
            detail = record["exceedance_detail"]
            self.assertIn("95th percentile", detail, record_id)
            self.assertIn("Figure 9", detail, record_id)

    def test_the_exceedance_names_the_population_and_its_bias(self):
        """A percentile over public-record losses is not a percentile over incidents."""
        for record_id in EXTREMES:
            detail = self.records[record_id]["exceedance_detail"]
            self.assertIn("PUBLIC RECORDS", detail, record_id)
            self.assertIn("not over all incidents", detail, record_id)

    def test_the_two_percentiles_are_kept_apart_on_the_record(self):
        """$32M is the pooled 95th; $28.5M is the 2024 90th. Neither is wrong.

        The publisher's own key findings put the $32M beside a 5-fold rise that
        belongs to the other one. Someone reconciling them later would "fix" a
        figure that is correct.
        """
        for record_id in EXTREMES:
            notes = self.records[record_id]["normalization_notes"]
            self.assertIn("90th percentile", notes, record_id)
            self.assertIn("28,500,000", notes, record_id)

    def test_the_median_records_say_which_median_they_are(self):
        for record_id in MEDIANS:
            limitations = self.records[record_id]["limitations"]
            self.assertIn("603,000", limitations, record_id)
            self.assertIn("2,900,000", limitations, record_id)
            self.assertIn("15.20x", limitations, record_id)
            self.assertIn("189,900", limitations, record_id)

    def test_the_five_fold_gap_between_the_two_medians_is_what_it_claims(self):
        """The records say ~4.8x. If the arithmetic is wrong, the caveat is wrong."""
        ratio = FIGURE_10_MEDIAN_2024 / FIGURE_9_MEDIAN
        self.assertAlmostEqual(ratio, 4.81, places=2)
        for record_id in MEDIANS:
            self.assertIn("4.8x", self.records[record_id]["limitations"], record_id)

    def test_the_publisher_figure_is_recorded_beside_our_rounding(self):
        """We store the page's "almost $3 million". The report prints $2.9M."""
        for record_id in MEDIANS:
            notes = self.records[record_id]["normalization_notes"]
            self.assertIn("2,900,000", notes, record_id)

    def test_no_shard_maximum_is_an_iris_2025_record(self):
        """A tripwire over the eleven shards, and the scope matters.

        **Corrected 2026-11-20.** When this was written the claim beside it was
        that all three $32M records are unselected comparison anchors. That is
        true of the **eleven shards** — which is all `build_portfolio_brackets`
        reports, so the assertion was never wrong — and false of the repository:
        `cyentia_iris_2025_extreme_security_incident_loss_usd` is `impact.max`
        for **two drift-watch scenarios**, `au_finance_insider_misuse` and
        `au_finance_third_party_outage`.

        So the `none_known` -> `modeled_quantile` correction did reach published
        exceedance statements, on two scenarios rather than none. That is a better
        outcome than was claimed and the claim was still wrong, which is why it is
        corrected here rather than left to read as an accident.

        The tripwire stands as written: if a *shard* maximum ever becomes an IRIS
        2025 record, the prose about comparison anchors has to be rewritten in the
        same change rather than going stale the way the two JP "selected as a
        bridge" notes did.
        """
        selected = {
            m.get("evidence_id") for m in build_portfolio_brackets(ROOT)["modules"]
        }
        self.assertEqual(selected & set(EXTREMES), set())


if __name__ == "__main__":
    unittest.main()
