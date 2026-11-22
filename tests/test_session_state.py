import json
import unittest
from datetime import date
from pathlib import Path

from engine.session_state import (
    BEGIN_MARKER,
    parse_porcelain_paths,
    END_LINE,
    current_release,
    parse_restart_point,
    recorded_fields,
    render_restart_point,
    restart_point_status,
    splice_restart_point,
)
from engine.doctor import restart_point_check


ROOT = Path(__file__).resolve().parents[1]


def flat(text):
    """The block is wrapped to the document's width; assert on its words."""
    return " ".join(text.split())


def sample_state(**overrides):
    state = {
        "generated_at": "2026-11-21",
        "git": {
            "branch": "main",
            "head": "0123456789abcdef0123456789abcdef01234567",
            "head_short": "0123456",
            "upstream": "origin/main",
            "ahead": 0,
            "behind": 0,
            "tree_clean": True,
            "dirty_count": 0,
            "local_branches": ["main"],
            "other_local_branches": [],
            "dirty_paths": [],
        },
        "release": {
            "release_id": "2026.11.20-v0.15.0",
            "release_version": "v0.15.0",
            "release_pack_fingerprint": "b5754a553527",
            "archive_present": True,
        },
        "pack_fingerprint": "b5754a553527",
        "tests": {"ran": True, "count": 647, "passed": True},
        "gates": {"evidence_errors": 0, "preflight_status": "pass"},
        "open_prs": 0,
        "doctor": {"status": "pass", "total": 20, "passing": 20, "not_passing": []},
    }
    state.update(overrides)
    return state


class RenderTests(unittest.TestCase):
    def test_the_block_states_what_the_restart_point_has_always_claimed(self):
        block = flat(render_restart_point(sample_state()))
        for fragment in [
            "measured 2026-11-21 at `0123456`",
            "`main` == `origin/main`",
            "tree clean",
            "No open PR.",
            "`v0.15.0` is the current release",
            "647 tests pass.",
            "Evidence clean, preflight clean.",
            "pass on all 20",
            "Data pack `b5754a553527`",
        ]:
            self.assertIn(fragment, block, fragment)

    def test_a_dirty_tree_and_a_red_suite_are_shouted_not_smoothed(self):
        block = flat(render_restart_point(sample_state(
            git={**sample_state()["git"], "tree_clean": False, "dirty_count": 3,
                 "dirty_paths": ["engine/a.py", "engine/b.py", "docs/internal/NEXT_STEPS.md"]},
            tests={"ran": True, "count": 647, "passed": False},
            doctor={"status": "needs_review", "total": 20, "passing": 19,
                    "not_passing": ["strength ledger (needs_review)"]},
        )))
        self.assertIn("**3 uncommitted path(s)**", block)
        self.assertIn("**647 tests ran and the suite failed.**", block)
        self.assertIn("**19 of 20**", block)
        self.assertIn("strength ledger (needs_review)", block)

    def test_its_own_uncommitted_file_is_named_not_counted(self):
        """At close the block is written before it is committed, so it is always dirty."""
        block = flat(render_restart_point(sample_state(
            git={**sample_state()["git"], "tree_clean": False, "dirty_count": 1,
                 "dirty_paths": ["docs/internal/NEXT_STEPS.md"]},
        )))
        self.assertIn("tree clean but for this file, uncommitted as written", block)
        self.assertNotIn("uncommitted path(s)", block)

    def test_a_missing_archive_says_the_citation_404s(self):
        state = sample_state()
        state["release"]["archive_present"] = False
        self.assertIn("a pinned citation 404s", flat(render_restart_point(state)))

    def test_an_uncounted_suite_is_labelled_not_run(self):
        block = flat(render_restart_point(
            sample_state(tests={"ran": False, "count": 647, "passed": None})))
        self.assertIn("647 tests collected (not run in this measurement)", block)
        self.assertNotIn("tests pass", block)

    def test_no_doctor_reading_means_no_doctor_sentence(self):
        """The first pass of a write renders without one; see write_restart_point."""
        block = flat(render_restart_point(sample_state(doctor=None)))
        self.assertNotIn("The doctor reads", block)
        self.assertIn("Data pack `b5754a553527`", block)

    def test_the_machine_readable_header_round_trips(self):
        state = sample_state()
        parsed = parse_restart_point(render_restart_point(state))
        self.assertEqual(parsed, recorded_fields(state))
        self.assertEqual(
            sorted(parsed),
            ["generated_at", "head", "pack_fingerprint", "release_version"],
        )

    def test_the_prose_cannot_disagree_with_the_header(self):
        """Both come from one dict, which is the whole reason the block is generated."""
        state = sample_state()
        block = render_restart_point(state)
        header = json.loads(block.split("state: ", 1)[1].split(" -->", 1)[0])
        prose = flat(block.split("-->", 1)[1])
        self.assertIn(header["release_version"], prose)
        self.assertIn(header["pack_fingerprint"], prose)
        self.assertIn(header["head"][:7], prose)

    def test_parse_returns_none_when_there_is_no_block(self):
        self.assertIsNone(parse_restart_point("## Restart point\n\nhand written, as it was.\n"))


class PorcelainTests(unittest.TestCase):
    """The columns cannot be trusted, and this is the bug that proved it.

    `_git` strips its stdout, which eats the leading space of an unstaged first
    line, so reading the path as `line[3:]` returned "cs/internal/NEXT_STEPS.md".
    The block reported "1 uncommitted path(s)" for a tree whose only change was
    the block itself — found by running the close ritual on 2026-11-22.
    """

    def test_the_stripped_first_line_still_yields_its_path(self):
        self.assertEqual(
            parse_porcelain_paths(["M docs/internal/NEXT_STEPS.md"]),
            ["docs/internal/NEXT_STEPS.md"],
        )

    def test_every_status_shape_in_this_repo_s_closes(self):
        self.assertEqual(
            parse_porcelain_paths([
                " M engine/doctor.py",
                "M  AGENTS.md",
                "MM tests/test_doctor.py",
                "?? engine/session_state.py",
                "A  scripts/session_state.py",
                " D docs/old.md",
                "",
            ]),
            ["engine/doctor.py", "AGENTS.md", "tests/test_doctor.py",
             "engine/session_state.py", "scripts/session_state.py", "docs/old.md"],
        )

    def test_a_rename_reports_where_the_file_landed(self):
        self.assertEqual(
            parse_porcelain_paths(["R  docs/a.md -> docs/b.md"]),
            ["docs/b.md"],
        )

    def test_a_quoted_path_loses_its_quotes(self):
        self.assertEqual(parse_porcelain_paths(['?? "docs/with space.md"']),
                         ["docs/with space.md"])


class SpliceTests(unittest.TestCase):
    DOC = (
        "# NEXT_STEPS\n\n## Pending on the owner\n\nowed things\n\n"
        "## Restart point\n\n"
        "**Narrative the generator does not own.**\n\n"
        "## History\n\nolder things\n"
    )

    def test_insert_goes_under_the_heading_and_keeps_the_prose(self):
        out = splice_restart_point(self.DOC, render_restart_point(sample_state()))
        self.assertIn("## Restart point\n\n" + BEGIN_MARKER, out)
        self.assertIn("**Narrative the generator does not own.**", out)
        self.assertIn("## History\n\nolder things", out)
        self.assertLess(out.index(BEGIN_MARKER), out.index("Narrative the generator"))

    def test_a_second_write_replaces_the_block_rather_than_stacking_them(self):
        once = splice_restart_point(self.DOC, render_restart_point(sample_state()))
        twice = splice_restart_point(once, render_restart_point(sample_state()))
        self.assertEqual(once, twice)
        self.assertEqual(twice.count(BEGIN_MARKER), 1)
        self.assertEqual(twice.count(END_LINE), 1)

    def test_rewriting_updates_the_facts_and_drops_the_old_ones(self):
        once = splice_restart_point(self.DOC, render_restart_point(sample_state()))
        later = splice_restart_point(once, render_restart_point(sample_state(
            generated_at="2026-12-01",
            release={"release_id": "2026.12.01-v0.16.0", "release_version": "v0.16.0",
                     "release_pack_fingerprint": "aaaabbbbcccc", "archive_present": True},
            pack_fingerprint="aaaabbbbcccc",
        )))
        self.assertIn("v0.16.0", later)
        self.assertNotIn("v0.15.0", later)
        self.assertNotIn("b5754a553527", later)
        self.assertIn("**Narrative the generator does not own.**", later)

    def test_a_document_with_no_restart_heading_is_refused(self):
        with self.assertRaises(ValueError):
            splice_restart_point("# NEXT_STEPS\n\nno heading here\n", "block\n")

    def test_an_unterminated_block_is_refused_rather_than_guessed(self):
        broken = self.DOC.replace("## Restart point\n\n",
                                  f"## Restart point\n\n{BEGIN_MARKER} oops\n")
        with self.assertRaises(ValueError):
            splice_restart_point(broken, "block\n")


class DriftTests(unittest.TestCase):
    def test_drift_is_reported_on_the_release_and_the_pack(self):
        document = splice_restart_point(SpliceTests.DOC, render_restart_point(sample_state()))
        status = restart_point_status(
            ROOT,
            document=document,
            live={"release_version": "v0.16.0", "pack_fingerprint": "aaaabbbbcccc"},
        )
        self.assertEqual(len(status["drift"]), 2)
        self.assertIn("v0.16.0", status["drift"][0])
        self.assertIn("aaaabbbbcccc", status["drift"][1])

    def test_matching_state_reports_no_drift(self):
        document = splice_restart_point(SpliceTests.DOC, render_restart_point(sample_state()))
        status = restart_point_status(
            ROOT,
            document=document,
            live={"release_version": "v0.15.0", "pack_fingerprint": "b5754a553527"},
        )
        self.assertEqual(status["drift"], [])
        self.assertEqual(status["recorded"]["generated_at"], "2026-11-21")

    def test_a_hand_written_restart_point_is_itself_the_drift(self):
        status = restart_point_status(
            ROOT,
            document="## Restart point\n\n**2026-11-20 session closed.** `main` at `4ebae5b`.\n",
            live={"release_version": "v0.15.0", "pack_fingerprint": "b5754a553527"},
        )
        self.assertIsNone(status["recorded"])
        self.assertEqual(len(status["drift"]), 1)
        self.assertIn("no generated restart point", status["drift"][0])

    def test_the_head_sha_and_test_count_are_not_compared(self):
        """The two fields a correct close commit invalidates are recorded, never pinned.

        Pinning a progress figure converts the next real advance into a failure,
        which this repository paid for twice (`flagged_verified == 4`, then `== 26`).
        The sha is worse than that: the commit that records the block changes it.
        """
        document = splice_restart_point(SpliceTests.DOC, render_restart_point(sample_state()))
        status = restart_point_status(
            ROOT,
            document=document,
            live={"release_version": "v0.15.0", "pack_fingerprint": "b5754a553527",
                  "head": "f" * 40},
        )
        self.assertEqual(status["drift"], [])


class LiveDocumentTests(unittest.TestCase):
    """Read the committed document, in the pattern tests/test_cell_coverage.py set.

    These assert that the block is present, generated and internally honest.
    They deliberately do **not** assert that it is current: a branch that moves
    the data pack is behind the restart point until the session closes, and the
    doctor's `restart point` check is where that is reported.
    """

    def test_next_steps_carries_exactly_one_generated_block(self):
        text = (ROOT / "docs" / "internal" / "NEXT_STEPS.md").read_text()
        self.assertEqual(text.count(BEGIN_MARKER), 1)
        self.assertEqual(text.count(END_LINE), 1)
        self.assertLess(text.index("## Restart point"), text.index(BEGIN_MARKER))

    def test_the_recorded_block_parses_and_is_complete(self):
        text = (ROOT / "docs" / "internal" / "NEXT_STEPS.md").read_text()
        recorded = parse_restart_point(text)
        self.assertIsNotNone(recorded)
        self.assertRegex(recorded["generated_at"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(recorded["head"], r"^[0-9a-f]{40}$")
        self.assertRegex(recorded["release_version"], r"^v\d+\.\d+\.\d+$")
        self.assertRegex(recorded["pack_fingerprint"], r"^[0-9a-f]{12}$")
        self.assertLessEqual(recorded["generated_at"], date.today().isoformat())

    def test_the_recorded_release_is_one_that_exists_on_disk(self):
        recorded = parse_restart_point((ROOT / "docs" / "internal" / "NEXT_STEPS.md").read_text())
        ids = [p.stem for p in (ROOT / "data_pack_releases").glob("*.json")]
        self.assertTrue(
            any(rid.endswith("-" + recorded["release_version"]) for rid in ids),
            f"{recorded['release_version']} names no release in data_pack_releases/",
        )

    def test_the_doctor_check_reads_the_committed_block(self):
        check = restart_point_check(ROOT)
        self.assertEqual(check["name"], "restart point")
        self.assertIn(check["status"], {"pass", "needs_review"})
        self.assertNotIn("no generated restart point", check["detail"])

    def test_the_block_does_not_record_itself_as_the_doctor_s_amber_line(self):
        """The bug the two-pass write exists to stop.

        The doctor's `restart point` check reads the block in the document, so a
        reading taken before the write describes the block being replaced. The
        first run of the generator recorded "19 of 20 - restart point
        (needs_review)" into the very block that cleared it.
        """
        text = (ROOT / "docs" / "internal" / "NEXT_STEPS.md").read_text()
        block = flat(text.split(BEGIN_MARKER, 1)[1].split(END_LINE, 1)[0])
        self.assertNotIn("restart point (needs_review)", block)

    def test_current_release_reads_the_newest_versioned_pack(self):
        release = current_release(ROOT)
        self.assertRegex(release["release_version"], r"^v\d+\.\d+\.\d+$")
        self.assertTrue(release["release_id"].endswith(release["release_version"]))
        self.assertTrue(release["archive_present"])


if __name__ == "__main__":
    unittest.main()
