import unittest
from pathlib import Path

from engine.benchmark_program import (
    build_benchmark_cohort_report,
    build_benchmark_program_report,
    build_benchmark_sprint_report,
    format_benchmark_cohort_report,
    format_benchmark_program_report,
    format_benchmark_sprint_report,
)
from engine.country_priorities import find_country_priority
from engine.taxonomy import load_taxonomies


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkProgramTests(unittest.TestCase):
    def test_benchmark_program_tracks_thirty_targets_without_overclaiming(self):
        report = build_benchmark_program_report(ROOT)
        output = format_benchmark_program_report(report)
        by_id = {target["id"]: target for target in report["targets"]}

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["target_count"], 30)
        self.assertEqual(report["module_seeded_count"], 11)
        self.assertEqual(report["benchmark_ready_count"], 6)
        self.assertEqual(report["status_counts"]["missing_module"], 19)
        self.assertEqual(report["status_counts"]["needs_evidence"], 5)
        self.assertIn("Benchmark-Grade 30 Shard Program", output)
        self.assertIn("benchmark-ready: 6", output)
        self.assertIn("ca_finance_data_breach_midmarket", by_id)
        self.assertIn("de_industrial_ransomware_midmarket", by_id)
        self.assertIn("sg_finance_bec_midmarket", by_id)
        self.assertIn("jp_manufacturing_ransomware_midmarket", by_id)
        self.assertIn("fr_finance_data_breach_midmarket", by_id)
        self.assertIn("us_finance_data_breach_midmarket", by_id)

    def test_existing_uk_breach_target_is_automated_benchmark_ready(self):
        report = build_benchmark_program_report(ROOT)
        by_id = {target["id"]: target for target in report["targets"]}
        target = by_id["gb_finance_data_breach_midmarket"]
        output = format_benchmark_program_report(report, target_id=target["id"])

        self.assertEqual(target["status"], "benchmark_ready")
        self.assertTrue(target["criteria"]["all_selected_parameters_source_backed"])
        self.assertTrue(target["criteria"]["selected_confidence_medium_or_high"])
        self.assertEqual(target["metrics"]["source_backed_parameters"], 6)
        self.assertEqual(target["metrics"]["confidence_medium_or_high_parameters"], 6)
        self.assertEqual(target["next_actions"], ["ready for human benchmark review"])
        self.assertIn("gb_finance_data_breach_midmarket", output)

    def test_seeded_cohort_report_ranks_large_upgrade_work(self):
        report = build_benchmark_program_report(ROOT)
        cohort = build_benchmark_cohort_report(report, "seeded")
        output = format_benchmark_cohort_report(cohort)
        by_id = {target["id"]: target for target in cohort["targets"]}

        self.assertEqual(cohort["cohort"]["title"], "Benchmark Cohort 1: seeded modules")
        self.assertEqual(cohort["status"], "needs_evidence")
        self.assertEqual(cohort["target_count"], 11)
        self.assertEqual(cohort["benchmark_ready_count"], 6)
        self.assertEqual(cohort["status_counts"]["benchmark_ready"], 6)
        self.assertEqual(cohort["status_counts"]["needs_evidence"], 5)
        # Queue is ascending by blocker_count; the 1-blocker tier is now the
        # industry-relevance trades (AU ransomware/data-breach). JP left the queue
        # on 2026-08-02 when its Japan frequency readings met the country minimum.
        self.assertEqual(cohort["upgrade_queue"][0]["blocker_count"], 1)
        self.assertNotIn(
            "jp_manufacturing_ransomware_midmarket",
            {u["id"] for u in cohort["upgrade_queue"]},
        )
        self.assertEqual(by_id["ca_finance_data_breach_midmarket"]["metrics"]["source_backed_parameters"], 6)
        self.assertEqual(by_id["ca_finance_data_breach_midmarket"]["blockers"], [])
        self.assertEqual(by_id["gb_finance_data_breach_midmarket"]["blockers"], [])
        # AU ransomware also carries an industry-relevance blocker on purpose
        # (2026-08-02): its frequency and impact anchors were reselected from
        # global financial-services benchmarks to Australia-resident all-sector
        # readings - shorter bridges for an Australian shard, but no longer
        # industry-matched. The shard was relabeled governed_starter to match.
        self.assertEqual(
            [b["code"] for b in by_id["au_finance_ransomware_midmarket"]["blockers"]],
            ["industry_relevance_gap"],
        )
        # AU data breach cleared its industry-relevance blocker on 2026-08-02:
        # impact.likely now uses IBM's 2026 Australian financial-services cell,
        # which is both country- and industry-matched.
        self.assertEqual(by_id["au_finance_data_breach_midmarket"]["blockers"], [])
        self.assertEqual(by_id["de_industrial_ransomware_midmarket"]["metrics"]["source_backed_parameters"], 6)
        self.assertEqual(by_id["de_industrial_ransomware_midmarket"]["blockers"], [])
        self.assertEqual(by_id["au_finance_bec_midmarket"]["metrics"]["source_backed_parameters"], 6)
        self.assertEqual(by_id["sg_finance_bec_midmarket"]["metrics"]["source_backed_parameters"], 6)
        self.assertIn("Upgrade queue", output)
        self.assertIn("au_finance_ransomware_midmarket", output)
        self.assertEqual(by_id["au_finance_data_breach_midmarket"]["metrics"]["source_backed_parameters"], 6)
        self.assertEqual(by_id["au_finance_data_breach_midmarket"]["metrics"]["confidence_medium_or_high_parameters"], 6)
        self.assertEqual(by_id["jp_manufacturing_ransomware_midmarket"]["blockers"], [])

    def test_seeded_sprint_report_groups_actionable_upgrade_work(self):
        report = build_benchmark_program_report(ROOT)
        sprint = build_benchmark_sprint_report(report, "seeded")
        output = format_benchmark_sprint_report(sprint)
        by_id = {target["id"]: target for target in sprint["targets"]}

        self.assertEqual(sprint["sprint"]["title"], "Seeded Evidence Upgrade Sprint A")
        self.assertEqual(sprint["status"], "needs_evidence_work")
        self.assertEqual(sprint["target_count"], 5)
        self.assertEqual(sprint["total_blocker_count"], 19)
        self.assertIn("frequency.max", sprint["focus_parameters"])
        self.assertIn("impact.max", sprint["focus_parameters"])
        self.assertNotIn("ca_finance_data_breach_midmarket", by_id)
        self.assertNotIn("de_industrial_ransomware_midmarket", by_id)
        self.assertIn("sg_finance_bec_midmarket", by_id)
        self.assertIn("au_finance_ransomware_midmarket", by_id)
        self.assertNotIn("au_finance_data_breach_midmarket", by_id)
        self.assertIn("Seeded Evidence Upgrade Sprint A", output)
        self.assertIn("Acceptance criteria", output)
        self.assertNotIn("jp_manufacturing_ransomware_midmarket", output)

    def test_norway_country_code_stays_string_not_yaml_boolean(self):
        countries = {item["id"] for item in load_taxonomies(ROOT / "taxonomies")["countries"]}
        norway = find_country_priority("NO")
        report = build_benchmark_program_report(ROOT)
        by_id = {target["id"]: target for target in report["targets"]}

        self.assertIn("NO", countries)
        self.assertIsNot(False, norway["country_id"])
        self.assertEqual(norway["country_id"], "NO")
        self.assertEqual(by_id["no_energy_ransomware_midmarket"]["context"]["country"], "NO")


if __name__ == "__main__":
    unittest.main()
