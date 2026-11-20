"""The Sophos manufacturing anchors carry the base they were read off.

The first record re-read under the ADR-0024 artifact-fit campaign (2026-11-20)
was `sophos_state_ransomware_manufacturing_2025`, chosen because it is the
anchor behind both `modeled_quantile` maxima in the portfolio — the DE and JP
manufacturing shards. `engine/artifact_fit.py` flagged its four records for
citing the publisher's blog page while a verified report sits in the manifest.

The quoted passages matched the held report exactly, so the flag was a citation
mismatch rather than an unread record. What the page could not show was the
base. Chart 8 reads **n=67 (2025), 157 (2024)**, so the published "18% of
payments were $5M or more, up from 15%" is about **12 organizations, up from
about 24** — the share rose while the count roughly halved, because the number
of manufacturing organizations disclosing a payment fell 57%. A reader taking
the 82nd percentile as a population statement is reading twelve responses.

ADR-0023 makes the denominator a declared property, and `limitations` renders
into the published `docs/EVIDENCE_REPORT.md`, so these figures are reader-facing
text. A number typed into prose has no owner — this module is the owner. It
pins what was verified against the publisher file, so a later edit that softens
or drops the base fails here rather than quietly reaching a reader.
"""
import unittest

from engine.project_paths import find_project_root
from engine.tail_bracket import load_evidence_records

ROOT = find_project_root()

SOURCE_ID = "sophos_state_ransomware_manufacturing_2025"

THRESHOLDS = (
    "sophos_manufacturing_ransomware_extreme_case_threshold_usd_2025",
    "sophos_manufacturing_ransomware_extreme_case_threshold_usd_2025_jp_context",
)
RECOVERIES = (
    "sophos_manufacturing_ransomware_recovery_cost_usd_2025",
    "sophos_manufacturing_ransomware_recovery_cost_usd_2025_jp_context",
)

# Read off the held report on 2026-11-20. sha256 c579c711f3004db660c547e4c73be6b0e4997cb5b76fffacabebacf928f99eae
PAYMENT_BASE_2025 = 67
PAYMENT_BASE_2024 = 157
PAYMENT_SHARE_2025 = 0.18
PAYMENT_SHARE_2024 = 0.15
RECOVERY_BASE = {2025: 332, 2024: 378, 2023: 205}
CHART_11_MANUFACTURING_USD = 1_270_000


def _records():
    return {r["id"]: r for r in load_evidence_records()}


class SophosManufacturingBaseTests(unittest.TestCase):
    def setUp(self):
        self.records = _records()
        for record_id in THRESHOLDS + RECOVERIES:
            self.assertIn(record_id, self.records, record_id)

    def test_the_four_records_still_belong_to_the_source_that_was_re_read(self):
        """If the source id moves, this module is pinning the wrong artifact."""
        for record_id in THRESHOLDS + RECOVERIES:
            self.assertEqual(self.records[record_id]["source_id"], SOURCE_ID, record_id)

    def test_no_value_moved_in_the_re_read(self):
        """The re-read corrected caveats and provenance. It moved no number."""
        for record_id in THRESHOLDS:
            self.assertEqual(self.records[record_id]["value"], 5_000_000, record_id)
            self.assertEqual(self.records[record_id]["parameter"], "impact.max", record_id)
        for record_id in RECOVERIES:
            self.assertEqual(self.records[record_id]["value"], 1_300_000, record_id)
            self.assertEqual(self.records[record_id]["parameter"], "impact.likely", record_id)

    def test_the_exceedance_basis_survived_the_re_read(self):
        """Checked against ADR-0008 expecting a mislabel; `modeled_quantile` holds.

        The ladder defines it as a stated percentile of a *fitted or published*
        loss distribution, and Chart 8 is a published banded distribution with
        the share stated in prose. `observed_rank` would be wrong: we have a
        band share, not the k-th largest of N.
        """
        for record_id in THRESHOLDS:
            self.assertEqual(
                self.records[record_id]["exceedance_basis"], "modeled_quantile", record_id
            )

    def test_the_payment_base_is_on_the_face_of_the_threshold_records(self):
        """Both fields, independently — not their concatenation.

        The first version of this test joined `limitations` and
        `exceedance_detail` before searching, and a mutation run proved it
        toothless: stripping the base from one field still passed, because the
        other carried it. Both fields reach readers on their own, so both are
        asserted on their own.
        """
        for record_id in THRESHOLDS:
            for field in ("limitations", "exceedance_detail"):
                text = self.records[record_id][field]
                self.assertIn("n=%d" % PAYMENT_BASE_2025, text, (record_id, field))
                self.assertIn("n=%d" % PAYMENT_BASE_2024, text, (record_id, field))

    def test_the_threshold_records_state_the_count_not_only_the_share(self):
        """18% of 67 is twelve organizations, and a share hides that.

        The base collapsed 157 -> 67 between editions, so the *share* rose while
        the *count* roughly halved. A record carrying only "up from 15%" tells a
        reader the opposite of what happened to the evidence.
        """
        self.assertEqual(round(PAYMENT_SHARE_2025 * PAYMENT_BASE_2025), 12)
        self.assertEqual(round(PAYMENT_SHARE_2024 * PAYMENT_BASE_2024), 24)
        for record_id in THRESHOLDS:
            detail = self.records[record_id]["exceedance_detail"]
            self.assertIn("about 12 organizations", detail, record_id)
            self.assertIn("about 24", detail, record_id)
            self.assertIn("57%", detail, record_id)

    def test_the_recovery_base_is_on_the_face_of_the_recovery_records(self):
        for record_id in RECOVERIES:
            limitations = self.records[record_id]["limitations"]
            for base in RECOVERY_BASE.values():
                self.assertIn("n=%d" % base, limitations, record_id)

    def test_the_recovery_records_no_longer_call_an_unqualified_average_a_mean(self):
        """The report says "average" here and "average (median)" elsewhere.

        It distinguishes the two, so asserting a mean resolved the publisher's
        silence in our own favour. The correction is the whole finding, and it
        reverses on any edit that reintroduces the word.
        """
        for record_id in RECOVERIES:
            record = self.records[record_id]
            for field in ("citation_detail", "extraction_notes"):
                text = record[field]
                self.assertNotIn("mean recovery", text, record_id)
                self.assertNotIn("mean ransomware", text, record_id)
                self.assertNotIn("mean cost", text, record_id)
            self.assertIn("AVERAGE", record["citation_detail"], record_id)

    def test_the_more_precise_chart_figure_is_recorded_rather_than_dropped(self):
        """We store the publisher's rounded prose figure; the chart is finer.

        Chart 11 puts manufacturing and production at USD 1.27M on the same
        n=332. Keeping the prose figure is defensible — it is what the publisher
        states — but discarding the knowledge that a finer one exists is not.
        """
        self.assertLess(CHART_11_MANUFACTURING_USD, 1_300_000)
        for record_id in RECOVERIES:
            self.assertIn("1.27M", self.records[record_id]["normalization_notes"], record_id)

    def test_the_re_read_is_dated_on_every_record_it_touched(self):
        """A claim about an artifact is only as good as the date it was checked."""
        for record_id in THRESHOLDS + RECOVERIES:
            text = " ".join(
                (self.records[record_id].get(field) or "")
                for field in ("limitations", "extraction_notes", "exceedance_detail")
            )
            self.assertIn("2026-11-20", text, record_id)


if __name__ == "__main__":
    unittest.main()
