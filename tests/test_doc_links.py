"""Every relative link in the documentation points at a file that exists.

Forty-seven were broken when this test was written (2026-09-27), through a suite that
was green the whole time. Forty-six of them were one mechanical event: an internal
working doc was moved into `docs/internal/archive/` and its relative links were never
re-based, so every `../adr/...` in it resolved one directory short. The forty-seventh
was worse because a reader hits it — `docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md` sent a
contributor to `../internal/strength_ledger.json`, which is `internal/` from `docs/`.

Neither is the kind of defect a careful writer avoids: a link is correct relative to
where its file sits, so *moving* a file breaks links nobody edited. That is why this is
a test rather than a habit. It is the documentation-shaped case of the rule in AGENTS.md —
if a claim cannot be generated, write the check that reads the document.

Anchors (`#section`) are deliberately not verified: the target's headings are prose and
a missing anchor degrades to landing at the top of the right file, which is a different
and much smaller failure than a 404.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: `[text](target)` — the only link form used in these docs.
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

#: Not our files to resolve: the web, mail, and same-page anchors.
EXTERNAL = ("http://", "https://", "mailto:", "#")

#: Directories that are not the project's own documentation.
SKIP_PARTS = {".venv", "node_modules", ".git"}


def markdown_files():
    return sorted(
        p for p in ROOT.rglob("*.md")
        if not SKIP_PARTS & set(p.parts)
    )


class DocumentationLinkTests(unittest.TestCase):
    def test_every_relative_link_resolves_to_a_file_that_exists(self):
        broken = []
        for path in markdown_files():
            text = path.read_text(encoding="utf-8")
            for match in LINK.finditer(text):
                target = match.group(1)
                if target.startswith(EXTERNAL):
                    continue
                relative = target.split("#", 1)[0]
                if not relative:
                    continue
                if not (path.parent / relative).resolve().exists():
                    line = text[: match.start()].count("\n") + 1
                    broken.append(
                        f"{path.relative_to(ROOT)}:{line} -> {target}")
        self.assertEqual(
            [], broken,
            "documentation links point at files that do not exist:\n  "
            + "\n  ".join(broken))

    def test_the_check_covers_the_documentation_it_claims_to(self):
        """A link test that silently stops finding files passes forever.

        The count is a floor rather than an equality so adding a doc does not fail the
        suite; it fails if the glob breaks or the tree is not where this expects.
        """
        files = markdown_files()
        self.assertGreaterEqual(
            len(files), 90,
            f"only {len(files)} markdown files found — the glob is no longer "
            "reaching the documentation tree")
        self.assertIn(ROOT / "README.md", files)
        self.assertIn(ROOT / "docs" / "ROADMAP.md", files)


if __name__ == "__main__":
    unittest.main()
