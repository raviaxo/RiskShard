"""The dispute path resolves: every judgment call links to a number that exists.

`docs/OPEN_JUDGMENT_CALLS.md` is where this project sends someone who wants to argue
with a number. The explorer links to it ("argue with an open judgment call"), the audit
page links to it, and `BASIS_OF_PREPARATION.md` points at it as the place decisions are
recorded rather than taken quietly. It is also, in its own words, *"maintained by hand at
each release"* — eight rows, each carrying a deep link of the form
`…/RiskShard/#<shard>/<parameter>` into the explorer.

Two things follow, and neither was checked before 2026-09-28.

**A deep link that stops resolving fails the one reader this project most wants.** A
dispute is half of milestone M5 and it has never happened once; sending that reader to a
page anchor that no longer exists is the cheapest possible way to lose them. Shards do
get renamed — `ADR-0004` exists because a rename must not break a citation, and the
explorer carries an alias table for exactly that — and `ADR-0018` retired an entire
published surface on measurement. Neither event would touch this file, which is what
makes it a test rather than a habit.

**`tests/test_doc_links.py` deliberately does not cover this.** It verifies that a
relative link resolves to a file and says in writing that anchors are not verified,
because a missing `#section` in prose degrades to landing at the top of the right page.
That reasoning is sound for prose and wrong here: these anchors are not navigation
inside a document, they are the address of the specific number under dispute, and
landing on the explorer with nothing highlighted is not a smaller failure, it is the
whole failure.

The row count is deliberately **not** asserted against a constant. Which calls a
practitioner could argue with is a judgment, not something the tree can generate, so a
hard-coded number here would be one more hand-maintained figure of exactly the kind that
drifted into `NEXT_STEPS.md` and made it say seven while the page said eight.
"""
import re
import unittest
from pathlib import Path

from engine.risk_modules import REQUIRED_PARAMETERS, load_risk_modules

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "OPEN_JUDGMENT_CALLS.md"

#: `https://raviaxo.github.io/RiskShard/#<shard>/<parameter>` — the explorer deep link
#: form documented in `scripts/explorer_template.html`: `#<shard-id>` addresses an item,
#: `#<shard-id>/<parameter>` a single line.
DEEP_LINK = re.compile(r"RiskShard/#([A-Za-z0-9_]+)/([A-Za-z0-9_.]+)")

#: A numbered row in the judgment-call table: `| 1 | … |`.
ROW = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)


class OpenJudgmentCallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PAGE.read_text(encoding="utf-8")
        cls.shards = {module["id"] for module in load_risk_modules()}

    def test_the_page_still_carries_judgment_calls(self):
        """A guard that passes on an empty table would be no guard at all."""
        self.assertTrue(ROW.findall(self.text), "no numbered rows found")

    def test_every_row_carries_a_deep_link_to_the_number(self):
        rows = ROW.findall(self.text)
        links = DEEP_LINK.findall(self.text)
        self.assertEqual(
            len(rows), len(links),
            f"{len(rows)} judgment-call rows but {len(links)} deep links — a row without "
            "one sends a would-be challenger to the page and no further")

    def test_every_deep_link_addresses_a_published_shard(self):
        """An unpublished shard has no explorer row, so a link to one resolves to nothing.

        This also keeps the page honest about scope: the third-party-outage starter
        carries the weakest anchors in the dataset, but it is not published in the
        explorer or in `/reports/`, so it does not belong here.
        """
        broken = [
            f"#{shard}/{parameter}" for shard, parameter in DEEP_LINK.findall(self.text)
            if shard not in self.shards
        ]
        self.assertEqual([], broken,
                         f"deep link(s) to a shard the explorer does not publish: {broken}")

    def test_every_deep_link_addresses_a_real_parameter_slot(self):
        broken = [
            f"#{shard}/{parameter}" for shard, parameter in DEEP_LINK.findall(self.text)
            if parameter not in set(REQUIRED_PARAMETERS)
        ]
        self.assertEqual([], broken,
                         f"deep link(s) to a parameter that is not a slot: {broken}")

    def test_rows_are_numbered_without_a_gap_or_repeat(self):
        """The numbers are how a disputant refers to a call, so they have to be stable."""
        numbers = [int(n) for n in ROW.findall(self.text)]
        self.assertEqual(list(range(1, len(numbers) + 1)), numbers)

    def test_the_surfaces_that_send_a_reader_here_still_do(self):
        """If the page stops being reachable, every guard above protects nothing."""
        for path in ("scripts/explorer_template.html", "scripts/audit_template.html"):
            with self.subTest(path=path):
                self.assertIn("OPEN_JUDGMENT_CALLS.md",
                              (ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
