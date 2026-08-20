"""The public audit page, pinned to the rules that make it worth publishing.

Roadmap M2. The page exists so a stranger can check the mode finding without
cloning the repo, which means the ways it could quietly mislead are the things
worth testing: a count without its denominator, an unread source rendered as a
source that publishes nothing, and a blocked answer rendered as a backlog item.
"""
import re
import unittest

from engine.project_paths import find_project_root
from engine.source_audit import (PROPERTIES, PROPERTY_PLAIN, PROPERTY_QUESTION,
                                 build_source_audit, manifest_hashes)
from scripts.build_audit_page import answer, main, render

ROOT = find_project_root()


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_source_audit(ROOT)
        cls.html = render(cls.audit, manifest_hashes(ROOT))

    def test_render_is_a_full_document_with_every_token_filled(self):
        self.assertTrue(self.html.lstrip().startswith("<!doctype"))
        self.assertIn("</body>", self.html)
        self.assertNotIn("__RS_", self.html)

    def test_every_registered_source_appears(self):
        for source in self.audit["sources"]:
            self.assertIn(f'id="{source["source_id"]}"', self.html,
                          f'{source["source_id"]} is registered and not on the page')

    def test_the_denominator_travels_with_the_count(self):
        """58 of 72 is the claim. "58 sources read" is how it gets quoted wrong.

        ADR-0015 requires the coverage be published beside any finding drawn from
        it, and this page is where a finding gets drawn from.
        """
        coverage = self.audit["coverage"]
        self.assertIn(f'{coverage["sources_fully_verified"]} of {coverage["sources"]}', self.html)
        self.assertIn(f'<b>{coverage["verified"]}</b> of {coverage["slots"]}', self.html)
        for phrase in ("answers blocked", "answers unread"):
            self.assertIn(phrase, self.html)

    def test_unread_and_blocked_are_never_rendered_as_a_no(self):
        """The whole audit rests on this distinction.

        A source nobody read is an open question. A source whose stored artifact is
        a landing page is blocked until the document is obtained. Neither is a
        source that publishes nothing, and a table is exactly where that collapses.
        """
        self.assertEqual(answer({"basis": "verified_against_artifact", "publishes": False})[0], "no")
        self.assertEqual(answer({"basis": "verified_against_artifact", "publishes": True})[0], "yes")
        self.assertEqual(answer({"basis": "no_readable_artifact"})[0], "blocked")
        self.assertEqual(answer({"basis": "unverified"})[0], "unread")
        self.assertEqual(answer({})[0], "unread")
        self.assertEqual(answer(None)[0], "unread")

        rendered = {label for label, _ in
                    (answer(s["properties"].get(p))
                     for s in self.audit["sources"] for p in PROPERTIES)}
        self.assertTrue({"blocked", "unread"} & rendered,
                        "no blocked or unread answer rendered: the distinction is untested")

    def test_the_page_states_what_bounds_its_own_answers(self):
        """The audit reads PDFs as extracted text, so a chart-only figure can be missed.

        That limitation belongs on the page rather than in a repo file nobody opens.
        """
        self.assertIn("extracted text", self.html)
        self.assertIn("chart image", self.html)
        self.assertIn("Blocked is not unread", self.html)

    def test_every_answer_carries_what_it_was_checked_against(self):
        """An answer with no artifact behind it is an opinion."""
        verified = [s for s in self.audit["sources"]
                    if any((s["properties"].get(p) or {}).get("basis") == "verified_against_artifact"
                           for p in PROPERTIES)]
        self.assertTrue(verified)
        self.assertIn("sha256", self.html)
        self.assertGreaterEqual(len(re.findall(r"read 20\d\d-\d\d-\d\d", self.html)), len(verified))

    def test_any_answer_can_be_disputed(self):
        """A page that cannot be argued with is a brochure."""
        self.assertIn("labels=audit-dispute", self.html)
        self.assertGreaterEqual(self.html.count("[dispute an answer]"), len(self.audit["sources"]))

    def test_the_mode_column_is_reported_with_its_read_count(self):
        """The headline finding must not appear as a bare zero."""
        read = self.audit["coverage"]["verified_by_property"]["mode"]
        self.assertIn(f"of {read} read", self.html)

    def test_check_mode_renders_without_writing(self):
        self.assertEqual(main(["--check"]), 0)


class TheAskIsReachableTests(unittest.TestCase):
    """ADR-0016 decided the ask is one audit row. Nobody had a route to give one.

    The barrier here was never that people looked and declined. It was that the
    four questions existed only in beta-PERT vocabulary, and there was no form to
    answer them in — so a willing reader had nothing to click. These tests pin the
    route, because a route is the whole contribution of this change.
    """

    TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "read_a_source.md"

    @classmethod
    def setUpClass(cls):
        cls.html = render(build_source_audit(ROOT), manifest_hashes(ROOT))
        cls.form = cls.TEMPLATE.read_text(encoding="utf-8")

    def test_every_question_has_a_plain_wording(self):
        self.assertEqual(set(PROPERTY_PLAIN), set(PROPERTIES))
        for prop, plain in PROPERTY_PLAIN.items():
            self.assertTrue(plain.strip(), prop)
            # plain means plain: the words that need a glossary stay in the technical line
            for jargon in ("beta-pert", "modal", "quantile", "population that"):
                self.assertNotIn(jargon, plain.lower(),
                                 f"{prop} plain wording still needs a glossary: {jargon!r}")

    def test_the_page_leads_with_plain_and_keeps_the_technical_wording(self):
        """Plain first so a reader can start; technical underneath so answers compare."""
        for prop in PROPERTIES:
            self.assertIn(PROPERTY_PLAIN[prop], self.html, f"{prop}: plain wording missing")
        self.assertIn(PROPERTY_QUESTION["mode"], self.html,
                      "the precise wording was dropped, so two answers stop being comparable")

    def test_the_page_offers_the_twenty_minute_ask_with_a_route(self):
        self.assertIn("template=read_a_source.md", self.html)
        self.assertIn("twenty minutes", self.html)

    # The load-bearing phrase of each plain question. Asserted against BOTH the plain
    # wording and the form, so the two cannot drift apart: reword a question and this
    # fails until the form is reworded with it.
    KEYPHRASE = {
        "mode": "most likely",
        "distribution": "spread",
        "exceedance": "how often losses go bigger",
        "population": "who was measured",
    }

    def test_the_form_asks_the_same_four_questions_as_the_page(self):
        self.assertTrue(self.TEMPLATE.exists(), "the ask has no form to answer it in")
        self.assertTrue(self.form.lstrip().startswith("---"), "issue template needs front matter")
        plain_form = self.form.replace("**", "")
        for prop in PROPERTIES:
            phrase = self.KEYPHRASE[prop]
            self.assertIn(phrase, PROPERTY_PLAIN[prop].lower(),
                          f"{prop}: the plain question no longer says {phrase!r}")
            self.assertIn(phrase, plain_form.lower(),
                          f"{prop}: the form and the page ask different questions")

    def test_the_form_makes_the_two_hard_answers_easy_to_give(self):
        """Both exist to stop a contributed row over-claiming.

        "I could not tell" is the answer a stranger will suppress in favour of a
        guess, and it is usually the informative one. And a reader has to know up
        front that an answer becomes `blocked` when we cannot obtain the document,
        or a blocked row reads as their work being rejected.
        """
        self.assertIn("could not tell", self.form)
        self.assertIn("blocked", self.form)

    def test_the_page_says_what_this_job_is(self):
        """It has no category name, so a reader has no slot to file it in."""
        self.assertIn("nobody checks", self.html.lower())


if __name__ == "__main__":
    unittest.main()

