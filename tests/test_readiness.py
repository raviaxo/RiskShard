import unittest
from pathlib import Path

from engine.data_packs import released_versions
from engine.readiness import build_readiness_dashboard, format_readiness_dashboard


ROOT = Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    def test_readiness_dashboard_summarizes_global_layers(self):
        dashboard = build_readiness_dashboard(
            ROOT,
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
        )

        self.assertGreaterEqual(dashboard["coverage"]["evidence_records"], 80)
        self.assertIn("ransomware", dashboard["coverage"]["threats"])
        self.assertIn("AU", dashboard["localization"]["covered_countries"])
        self.assertIn("CA", dashboard["localization"]["covered_countries"])
        self.assertIn("DE", dashboard["localization"]["covered_countries"])
        self.assertIn("FR", dashboard["localization"]["covered_countries"])
        self.assertIn("GB", dashboard["localization"]["covered_countries"])
        self.assertIn("JP", dashboard["localization"]["covered_countries"])
        self.assertIn("SG", dashboard["localization"]["covered_countries"])
        self.assertTrue(dashboard["install_release"]["pyproject"])
        self.assertEqual(len(dashboard["data_pack"]["fingerprint"]), 64)
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)
        self.assertEqual(dashboard["scenarios"]["stage_counts"]["governed_starter"], 15)
        self.assertEqual(dashboard["scenarios"]["stage_counts"]["demo_fixture"], 5)
        self.assertEqual(dashboard["risk_modules"]["module_count"], 11)
        self.assertEqual(dashboard["evidence_packs"]["pack_count"], 11)
        self.assertEqual(len(dashboard["evidence_packs"]["coverage_matrix"]), 11)
        gb = next(
            row for row in dashboard["evidence_packs"]["coverage_matrix"]
            if row["module_id"] == "gb_finance_data_breach_midmarket"
        )
        ca = next(
            row for row in dashboard["evidence_packs"]["coverage_matrix"]
            if row["module_id"] == "ca_finance_data_breach_midmarket"
        )
        self.assertEqual(gb["source_backed_direct"], 6)
        self.assertEqual(gb["assumption_only_direct"], 0)
        self.assertEqual(gb["next_gap"], "ready for practitioner review")
        self.assertEqual(ca["source_backed_direct"], 6)
        self.assertEqual(ca["assumption_only_direct"], 0)
        self.assertEqual(ca["next_gap"], "review medium-confidence source-backed evidence")
        self.assertEqual(
            dashboard["readiness_gate"]["status"],
            "ready_for_local_calibrated_run",
        )
        self.assertEqual(dashboard["feed_governance"]["problem_feeds"], [])
        # Not a count. This asserted ">= 2 actions" until 2026-09-27, and it only ever
        # held because "cut a named data-pack release" was appended unconditionally —
        # the list was padded by an action that was already done. An empty plate is a
        # legitimate state for this dashboard to report, so what is checked is that
        # every action it does report is well formed and ordered.
        actions = dashboard["next_actions"]
        self.assertTrue(
            all({"priority", "area", "title", "detail", "command"} <= set(a)
                for a in actions),
            "a next action is missing one of its fields")
        self.assertTrue(
            all(a["priority"] in {"P0", "P1", "P2", "P3"} for a in actions),
            "a next action carries an unknown priority")
        priorities = [a["priority"] for a in actions]
        self.assertEqual(priorities, sorted(priorities),
                         "next actions are not ordered by priority")
        if actions:
            self.assertNotEqual(actions[0]["priority"], "P0")

    def test_readiness_dashboard_formats_for_console(self):
        dashboard = build_readiness_dashboard(ROOT)
        output = format_readiness_dashboard(dashboard)

        self.assertIn("Global readiness dashboard", output)
        self.assertIn("Gate: ready_for_local_calibrated_run", output)
        self.assertIn("Next actions", output)
        self.assertIn("Data pack:", output)
        self.assertIn("Scenarios: demo_fixture=5, governed_starter=15", output)
        self.assertIn("Risk modules: 11", output)
        self.assertIn("Evidence packs: 11", output)
        self.assertIn("Module coverage matrix", output)
        self.assertIn("ca_finance_data_breach_midmarket: 6/6 source-backed", output)
        self.assertIn("de_industrial_ransomware_midmarket: 6/6 source-backed", output)
        self.assertIn("sg_finance_bec_midmarket: 6/6 source-backed", output)
        self.assertIn("gb_finance_data_breach_midmarket: 6/6 source-backed", output)
        self.assertIn("Installable package: True", output)


class ReleaseAdviceTests(unittest.TestCase):
    """The dashboard must not advise cutting a release this pack already has.

    It did, on every run, from the day the action was added until 2026-09-27 — including
    the run minutes after v0.12.0 was tagged from the live fingerprint. Every other
    action in `next_actions` fires on a condition; this one had none.
    """

    def test_the_live_advice_tracks_the_live_release_state(self):
        """Whether the advice appears has to follow the tree, in both directions.

        This asserted `pack["released_as"]` outright until 2026-09-28, which made it a
        claim about the repository's release state rather than about the code: the
        working tree's fingerprint moves the moment any pack content is edited, so the
        suite went red on every content change until a release was cut, and the only
        ways to green it were to cut a release for the sake of the gate or to skip the
        gate. The condition being guarded is the conditioning itself, and that is what
        this now checks — on whichever branch the live tree is on. Both branches are
        also pinned deterministically below, so neither depends on today's state.
        """
        dashboard = build_readiness_dashboard(ROOT)
        pack = dashboard["data_pack"]
        titles = [a["title"] for a in dashboard["next_actions"]]
        if pack["released_as"]:
            self.assertNotIn("Cut a named data-pack release", titles)
        else:
            self.assertIn("Cut a named data-pack release", titles)

    def test_a_released_fingerprint_does_not_get_the_advice(self):
        """The mirror of the test below, so the "released" branch is always exercised.

        Without it, the advice-absent case was only ever checked against whatever state
        the working tree happened to be in.
        """
        from engine.readiness import next_actions

        dashboard = build_readiness_dashboard(ROOT)
        dashboard["data_pack"] = dict(
            dashboard["data_pack"], released_as=["2026.09.27-v0.12.0"])
        titles = [a["title"] for a in next_actions(dashboard)]
        self.assertNotIn("Cut a named data-pack release", titles)

    def test_an_unreleased_fingerprint_still_gets_the_advice(self):
        """The guard must not silence the action, only condition it."""
        from engine.readiness import next_actions

        dashboard = build_readiness_dashboard(ROOT)
        dashboard["data_pack"] = dict(dashboard["data_pack"], released_as=[])
        titles = [a["title"] for a in next_actions(dashboard)]
        self.assertIn("Cut a named data-pack release", titles)

    def test_a_release_is_matched_on_fingerprint_not_on_filename(self):
        """A citation pins the fingerprint, so that is what "released" has to mean."""
        self.assertEqual(
            [], released_versions("not-a-real-fingerprint",
                                  ROOT / "data_pack_releases"))
        self.assertEqual(
            [], released_versions("anything", ROOT / "no_such_directory"))


if __name__ == "__main__":
    unittest.main()
