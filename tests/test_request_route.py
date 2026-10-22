"""The advertised contribution routes end where they say they end.

`CONTRIBUTING.md` lists "Request a shard" as route 1 — *"zero research required"*, the
easiest way in, and the first thing a new reader is offered. The explorer repeats it in
the notice-to-readers block, the issue template repeats it, and
`docs/REQUESTED_SHARDS.md` is the page it all points at.

All four said, until 2026-09-29, that requests decide what gets built next.

**That had been false since 2026-08-22**, and the authority for it was the ADR that
retired it. [ADR-0016](../docs/adr/0016-the-audit-is-the-product.md) part 2 froze shard
coverage at 11 on 2026-08-15 — *"No new cells, no new countries, no new threats"* — and
[ADR-0006](../docs/adr/0006-depth-over-breadth.md)'s 2026-08-22 amendment withdrew its own
reopening trigger in as many words: *"ADR-0016 part 1 declines a new cell however it
arrives, and `docs/REQUESTED_SHARDS.md` is no longer a route to one."* `CONTRIBUTING.md`
cited ADR-0006 as grounds for the promise the amendment had just withdrawn. Two further
documents — `docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md` end to end, and three sections of
`docs/CONTENT_CONTRIBUTION.md` — walked a contributor through building a new cell that
would be declined on arrival. Six surfaces, 38 to 45 days stale, nothing watching any of
them.

**Why this is worth a test rather than a correction.** The project already knows that a
hand-written claim rots: the README sold a framing ADR-0010 had retired for three months,
and the social card carried a retired headline for twelve days. This one is worse than
either, because it is not a description that went stale — it is a **promise made to the
one audience the project needs**, on the route it advertises as easiest. A reader who
takes it spends their two minutes and is declined. M5 counts exactly this reader.

**The assertions run in whichever direction the tree is in.** This deliberately copies the
fix applied to `tests/test_readiness.py` on 2026-09-28, where a check asserted a fact about
repository state and so could not pass during normal work. If the freeze lifts — a second
maintainer, or genuinely per-cell impact evidence, the two triggers ADR-0006's amendment
left standing — the disclosures below become the stale copy and the test says so, instead
of pinning prose that has itself gone out of date. The freeze is read from ADR-0016 rather
than hard-coded here, so there is one owner for it.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUEST_TEMPLATE = "template=request_a_shard.md"

# Live contributor-facing surfaces.
#
# The explorer is pinned at `scripts/explorer_template.html`, not at `docs/index.html`.
# The rendered page is gitignored and built at deploy, so asserting on it would be a check
# that passes only on a machine that has run the build — the same shape as the
# `tests/test_readiness.py` assertion fixed on 2026-09-28, which made a claim about
# repository state rather than about the code. The template is the tracked source and the
# CTA is static text in it, so pinning the template pins what ships.
#
# `docs/r/` is excluded on purpose: those are archived releases pinned by citation, and
# rewriting what a past release said is the one thing a citation archive must never do.
SURFACES = (
    Path("CONTRIBUTING.md"),
    Path("docs/REQUESTED_SHARDS.md"),
    Path("scripts/explorer_template.html"),
    Path(".github/ISSUE_TEMPLATE/request_a_shard.md"),
)

# Phrasings that assert a request produces a shard. Each was live on 2026-09-29.
RETIRED_PROMISES = (
    "requests decide what gets built next",
    "demand signal that decides which cells get built",
    "demand signal that decides what gets built next",
    "no shard is added without demand",
    "become the next objective in the internal queue",
    "the project doesn't add shards nobody asked for",
)

# Every surface must disclose the freeze in its own words; these are the load-bearing
# fragments, not a style rule.
DISCLOSURE = re.compile(
    r"frozen at 11|freezes at 11|coverage is frozen|does not currently produce a shard"
    r"|will not be built|declined however",
    re.IGNORECASE,
)


# The one place a retired promise may still appear, and the exact words it may appear in.
QUOTED_WITHDRAWALS = {
    "REQUESTED_SHARDS.md": (
        '*"repeated or strong requests become the next objective in the internal '
        'queue,"*',
    ),
}


def read(relpath):
    return (ROOT / relpath).read_text(encoding="utf-8")


def collapse(text):
    """Flatten wrapping so a quoted sentence broken across lines still matches."""
    return re.sub(r"\s+", " ", text)


def shard_coverage_is_frozen():
    """Read the freeze off ADR-0016 rather than restating it here.

    One canonical owner (AGENTS.md): if part 2 is ever superseded, this returns False and
    the disclosure assertions invert rather than holding prose that has gone stale.
    """
    adr = read("docs/adr/0016-the-audit-is-the-product.md")
    status = adr.split("\n")[2]
    if "Superseded" in status or "Withdrawn" in status:
        return False
    return "### 2. Shard coverage freezes at 11" in adr


class FreezeIsStillTheDecision(unittest.TestCase):
    def test_adr_0016_part_2_is_the_owner_of_the_freeze(self):
        """The premise every other assertion in this file rests on."""
        adr = read("docs/adr/0016-the-audit-is-the-product.md")
        self.assertIn("### 2. Shard coverage freezes at 11", adr)
        self.assertIn("No new cells, no new countries, no new threats", adr)

    def test_adr_0006_amendment_withdrew_demand_as_a_trigger(self):
        """The sentence that made six surfaces false, quoted where it lives."""
        adr = read("docs/adr/0006-depth-over-breadth.md")
        self.assertIn("is no longer a route to one", adr)
        self.assertIn("declines a new cell however it arrives", adr)


class RequestRouteTellsTheTruth(unittest.TestCase):
    def test_every_surface_offering_the_form_discloses_the_freeze(self):
        """Offer the form and you owe the reader the freeze, in the same place."""
        if not shard_coverage_is_frozen():
            self.skipTest("ADR-0016 part 2 no longer freezes coverage")
        for relpath in SURFACES:
            with self.subTest(surface=str(relpath)):
                text = read(relpath)
                if REQUEST_TEMPLATE not in text and relpath.name != "request_a_shard.md":
                    continue
                self.assertRegex(
                    text,
                    DISCLOSURE,
                    f"{relpath} offers the shard-request route without saying coverage "
                    "is frozen. A reader who takes it will be declined.",
                )

    def test_no_live_surface_repeats_a_retired_promise(self):
        """The exact phrasings that were live on 2026-09-29, kept out by name.

        One exemption, spelled out rather than pattern-matched: `REQUESTED_SHARDS.md`
        quotes its own retired promise inside the paragraph withdrawing it, because a
        withdrawal that paraphrases what it withdraws is the quiet kind this project
        does not write (AGENTS.md: caveats get louder, not quieter). The exemption is
        the full quoted sentence, so it cannot widen into cover for a promise that
        drifts back in beside it.
        """
        if not shard_coverage_is_frozen():
            self.skipTest("ADR-0016 part 2 no longer freezes coverage")
        for relpath in SURFACES:
            flat = collapse(read(relpath))
            allowed = QUOTED_WITHDRAWALS.get(relpath.name, ())
            for promise in RETIRED_PROMISES:
                with self.subTest(surface=str(relpath), promise=promise):
                    occurrences = flat.count(promise)
                    if not occurrences:
                        continue
                    exempt = sum(
                        collapse(quote).count(promise)
                        for quote in allowed
                        if collapse(quote) in flat
                    )
                    self.assertEqual(
                        occurrences,
                        exempt,
                        f"{relpath} states '{promise}' outside a quoted withdrawal; "
                        "ADR-0016 part 2 retired it.",
                    )

    def test_the_request_page_does_not_ask_for_an_impossible_label(self):
        """It told outside contributors to apply `requested-shard` themselves.

        Labelling an issue needs triage permission, which is exactly what the audience
        this page addresses does not have — the same class of defect ADR-0022 found in
        the loss-event route, where the contribution path was structurally closed rather
        than merely undocumented. The template applies the label itself.
        """
        text = read("docs/REQUESTED_SHARDS.md")
        self.assertNotRegex(
            text,
            r"tag it `requested-shard`",
            "an outside contributor cannot apply a label",
        )
        self.assertIn(REQUEST_TEMPLATE, text, "the page must link the purpose-built form")

    def test_the_template_that_carries_the_label_is_the_one_linked(self):
        """`shard_or_source.md` labels `data`; only `request_a_shard.md` labels demand."""
        template = read(".github/ISSUE_TEMPLATE/request_a_shard.md")
        self.assertIn("labels: requested-shard", template)


class ClosedRoutesSaySo(unittest.TestCase):
    """Two documents walk a contributor through building a cell that is declined.

    Kept rather than deleted — the tooling still runs and the benchmark programme is how
    the existing 11 targets were chosen — so the banner is what stops them reading as an
    invitation.
    """

    def test_benchmark_workflow_is_marked_closed(self):
        if not shard_coverage_is_frozen():
            self.skipTest("ADR-0016 part 2 no longer freezes coverage")
        text = read("docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md")
        self.assertIn("CLOSED", text.split("\n")[0])
        self.assertIn("0016-the-audit-is-the-product.md", text)

    def test_new_cell_sections_are_marked_closed(self):
        if not shard_coverage_is_frozen():
            self.skipTest("ADR-0016 part 2 no longer freezes coverage")
        text = read("docs/CONTENT_CONTRIBUTION.md")
        for heading in (
            "## Country Pack Checklist",
            "## Risk Module Checklist",
            "## Scaffold A New Pack",
        ):
            with self.subTest(heading=heading):
                line = next(l for l in text.split("\n") if l.startswith(heading))
                self.assertIn("CLOSED", line, f"{heading} still reads as an open route")


if __name__ == "__main__":
    unittest.main()
