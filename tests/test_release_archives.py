"""Every versioned release has the archive a pinned citation resolves to.

`docs/CITING.md` makes one promise to anyone who quotes a number from this project:

    A pinned citation keeps resolving to the value it was written against, at
    https://raviaxo.github.io/RiskShard/r/<release>/, even after the live figure moves.

That promise is kept by a **committed** directory, not a generated one.
`scripts/build_explorer.py --archive` writes `docs/r/<release>/index.html` and refuses to
overwrite an existing one, because a pinned citation must keep resolving to what it
resolved to; `.github/workflows/pages.yml` lists `docs/r/**` among its triggers and says
in a comment that without it "an archive-only commit never deploys and pinned citations
404 until the next unrelated deploy".

Nothing checked that the archive was ever written. **v0.12.0 was tagged and released on
2026-09-27 with no archive**, so for a day `…/r/2026.09.27-v0.12.0/` returned 404 — a
pinned citation against the current release, the one whose headline is *"the audit is
complete, of the obtainable corpus"*, resolved to nothing. Every gate was green, because
cutting a release and archiving it were two steps and only the first had a check.

Two invariants, and the second matters more than it looks:

1. **A versioned release has an archive.** Unversioned packs are the two pre-`v0.1.0`
   working packs listed below; they were never tagged, so their tree cannot be
   reconstructed and an archive for them would have to be built from some later tree.
   A wrong archive is worse than a missing one, so they are declared rather than
   backfilled — and a *new* unversioned pack fails this test instead of quietly joining
   them.
2. **An archive embeds its own release id.** This is the failure the first invariant
   invites: the fix for a missing archive is to build one, and building it from `HEAD`
   rather than from the tag produces a file that says one release and contains another.
   The v0.12.0 archive was built from a worktree at the tag for exactly this reason.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "data_pack_releases"
ARCHIVES = ROOT / "docs" / "r"

#: `…-v1.2.3`, optionally with a suffix such as `-stable`.
VERSIONED = re.compile(r"-v\d+\.\d+\.\d+")

#: The release id the explorer inlined into its own data payload.
EMBEDDED_RELEASE = re.compile(r'"release":"([^"]+)"')

#: Working packs cut before `v0.1.0` and never tagged — see the module docstring.
UNVERSIONED_BY_HISTORY = frozenset({
    "2026.07.14-beta-public-readiness",
    "2026.07.20-us-bec-source-backed",
})


def release_ids():
    return sorted(p.stem for p in RELEASES.glob("*.json"))


class ReleaseArchiveTests(unittest.TestCase):
    def test_there_are_releases_to_check(self):
        """A guard that passes on an empty directory would be no guard at all."""
        self.assertTrue(release_ids())

    def test_every_versioned_release_has_an_archive(self):
        missing = [
            rid for rid in release_ids()
            if VERSIONED.search(rid) and not (ARCHIVES / rid / "index.html").is_file()
        ]
        self.assertEqual(
            [], missing,
            "released but not archived, so a pinned citation 404s: "
            f"{missing} — build it from a worktree at the tag, not from HEAD")

    def test_the_only_unversioned_packs_are_the_two_declared_ones(self):
        """A new unversioned pack has to be a decision, not a silent exemption."""
        unversioned = {rid for rid in release_ids() if not VERSIONED.search(rid)}
        self.assertEqual(
            UNVERSIONED_BY_HISTORY, unversioned,
            "an unversioned data pack appeared; decide whether it is citable and "
            "archive it, or record why it is not")

    def test_every_archive_says_which_release_it_is(self):
        """An archive that embeds a different release is worse than a missing one."""
        wrong = []
        for directory in sorted(p for p in ARCHIVES.iterdir() if p.is_dir()):
            page = directory / "index.html"
            if not page.is_file():
                wrong.append(f"{directory.name}: no index.html")
                continue
            found = EMBEDDED_RELEASE.search(page.read_text(encoding="utf-8",
                                                           errors="replace"))
            if not found:
                wrong.append(f"{directory.name}: no release in payload")
            elif found.group(1) != directory.name:
                wrong.append(f"{directory.name}: embeds {found.group(1)}")
        self.assertEqual([], wrong, f"archive/release mismatch: {wrong}")

    def test_every_archive_belongs_to_a_release_that_exists(self):
        """The reverse direction: an archive for a pack nobody can verify against."""
        known = set(release_ids())
        orphans = [p.name for p in sorted(ARCHIVES.iterdir())
                   if p.is_dir() and p.name not in known]
        self.assertEqual([], orphans, f"archive with no data-pack release: {orphans}")

    def test_the_deploy_watches_the_archive_directory(self):
        """A committed archive that never deploys keeps 404ing, which is the same bug."""
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8")
        self.assertIn("docs/r/**", workflow)

    def test_citing_still_promises_the_path_these_archives_serve(self):
        """If the promise moves, these guards are protecting the wrong directory."""
        citing = (ROOT / "docs" / "CITING.md").read_text(encoding="utf-8")
        self.assertIn("/RiskShard/r/<release>/", citing)


if __name__ == "__main__":
    unittest.main()
