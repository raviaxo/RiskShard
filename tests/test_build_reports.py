"""The published executive summaries.

The report has existed since v0.3.0 and lived only in the console: to see one you
had to clone the repository and start an interactive session. Publishing it is the
cheapest thing this project can do that a practitioner would actually take away —
and the only reason it is worth taking is the disclosure added in v0.11.0, which
says *who the evidence was measured on* rather than only that it is published.

These tests are deliberately cheap. Rendering all eleven runs eleven seeded
simulations, so the expensive path is exercised once and the rest is checked
structurally.
"""
import re
import unittest

from engine.project_paths import find_project_root
from engine.provenance import build_portfolio_provenance

ROOT = find_project_root()


def _one_report():
    from engine.evidence_packs import build_evidence_pack_registry
    from engine.executive_report import build_executive_report
    from engine.web_console import WebConsoleApp

    app = WebConsoleApp(root=ROOT)
    app.run_command("use us_finance_data_breach_midmarket")
    app.run_command("run")
    console = app.console
    module = console.current_module()
    registry = build_evidence_pack_registry(ROOT, module_id=module["id"])
    pack = registry["packs"][0] if registry["packs"] else {}
    return build_executive_report(console.last_run, module, pack, root=ROOT)


class HtmlFormatterTests(unittest.TestCase):
    """One content source, two renderings. They must not be able to disagree."""

    @classmethod
    def setUpClass(cls):
        from engine.executive_report import (format_executive_report_html,
                                             format_executive_report_markdown)
        cls.report = _one_report()
        cls.markdown = format_executive_report_markdown(cls.report)
        cls.html = format_executive_report_html(cls.report)

    def _text(self):
        """The page as a reader sees it: tags removed AND entities resolved.

        Without the unescape, an apostrophe in the source reads as `&#x27;` here and
        every sentence containing one looks lost.
        """
        import html as _h
        return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", self.html)))

    def test_every_line_of_the_markdown_survives_into_the_page(self):
        """The converter is purpose-built for this document, so this is the check that
        it actually covers it: no sentence may be silently dropped.

        Compared with all whitespace removed. Stripping tags to get the page's text
        leaves a space wherever inline formatting ended mid-sentence — "exact context"
        followed by "</b>," becomes "exact context ," — so matching on prose spacing
        tests the tag-stripper rather than the converter.
        """
        def squeeze(value):
            return re.sub(r"\s+", "", value)

        text = squeeze(self._text())
        for line in self.markdown.split("\n"):
            stripped = re.sub(r"^\s*[-#>]+\s*", "", line)
            stripped = re.sub(r"[*`|]", "", stripped).strip()
            if len(stripped) < 25:
                continue
            probe = squeeze(stripped)[:60]
            self.assertIn(probe, text, f"lost from the HTML: {stripped[:70]!r}")

    def test_the_disclosure_reaches_the_page(self):
        text = self._text()
        self.assertIn("What the figure rests on", text)
        self.assertIn("says the evidence is published; this says who it was measured on", text)

    def test_markup_is_structural_rather_than_escaped_text(self):
        for tag in ("<h1>", "<h2>", "<table>", "<ul>", "<b>", "<code>"):
            self.assertIn(tag, self.html, tag)
        self.assertNotIn("**", self._text(), "raw Markdown emphasis leaked into the page")

    def test_content_is_escaped_before_it_is_formatted(self):
        from engine.executive_report import format_executive_report_html
        spiked = dict(self.report)
        spiked["title"] = 'Shard <script>alert("x")</script>'
        self.assertNotIn("<script>", format_executive_report_html(spiked))


class PageBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.build_reports import latest_release, render, render_index
        cls.report = _one_report()
        cls.release = latest_release()
        cls.page = render(cls.report, cls.release)
        cls.index = render_index([cls.report], cls.release)

    def test_no_template_token_survives(self):
        for name, markup in (("page", self.page), ("index", self.index)):
            self.assertNotIn("__RS_", markup, f"unfilled token in the {name}")

    def test_the_markup_is_balanced(self):
        """A stray closing tag is invisible in the HTML and obvious on the page.

        The index shipped with `</p>` where a `</div>` belonged, so the callout's rule
        ran the full height of the document. Nothing caught it but looking at it, and
        a generated page that nobody looks at needs this instead.
        """
        for name, markup in (("page", self.page), ("index", self.index)):
            body = markup[markup.index("<body>"):]
            for tag in ("div", "table", "ul", "tbody"):
                opened = len(re.findall(rf"<{tag}\b", body))
                closed = len(re.findall(rf"</{tag}>", body))
                self.assertEqual(opened, closed,
                                 f"{name}: {opened} <{tag}> against {closed} </{tag}>")

    def test_the_page_is_pinned_to_a_release(self):
        """A board summary with no release on it cannot be checked later."""
        self.assertTrue(self.release, "no data-pack release found to pin against")
        self.assertIn(self.release, self.page)

    def test_the_page_links_back_to_the_evidence_and_the_audit(self):
        self.assertIn(f'#{self.report["module_id"]}', self.page)
        self.assertIn("audit.html", self.page)

    def test_the_index_leads_with_the_measured_share_not_the_money(self):
        """The number a reader should distrust first is how much of the figure was
        measured on their context, so it is a column rather than a footnote."""
        self.assertIn("Measured here", self.index)
        self.assertIn("No shard in this portfolio is well anchored on both", self.index)

    def test_the_summaries_are_not_sold_as_benchmark_grade(self):
        """The maturity ladder has to survive onto a page a board might read.

        The two surfaces say it differently and both must keep saying it: the report
        carries the shard's own status caveat, the index says it once for all eleven.
        """
        self.assertIn("not a human-approved benchmark", self.page)
        self.assertIn("not benchmark-grade", self.index)


class DeploymentTests(unittest.TestCase):
    """A generated page nothing deploys is a page nobody reads."""

    @classmethod
    def setUpClass(cls):
        cls.workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        cls.ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    def test_the_deploy_builds_them(self):
        self.assertIn("python scripts/build_reports.py", self.workflow)

    def test_a_change_to_the_builder_triggers_a_deploy(self):
        for path in ("scripts/build_reports.py", "scripts/report_template.html",
                     "scripts/report_index_template.html"):
            self.assertIn(path, self.workflow, f"{path} does not trigger a redeploy")

    def test_they_are_generated_at_deploy_and_never_committed(self):
        """Same posture as docs/index.html. A committed board summary can drift from
        the evidence it summarises, and this one carries dollar figures."""
        self.assertIn("docs/reports/", self.ignore)

    def test_every_published_shard_gets_one(self):
        from scripts.build_reports import main  # noqa: F401  (import must not explode)
        module_ids = [m["module_id"] for m in build_portfolio_provenance(ROOT)["modules"]]
        self.assertEqual(len(module_ids), 11)
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        self.assertIn("reports/'+esc(s.id)+'.html", template,
                      "the filing does not link each item to its summary")


if __name__ == "__main__":
    unittest.main()
