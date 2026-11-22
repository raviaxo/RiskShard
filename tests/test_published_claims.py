"""Public documents are checked against the tools that own their numbers.

Written 2026-11-22 after auditing `README.md` claim by claim against the tool
behind each one. Five claims were wrong and the suite was green throughout:

* the measurement vocabulary was described as **18 entries** two days after
  ADR-0028 made it 19;
* the chance a single event exceeds AUD 20M was published as **23%** in two
  places, where the worked decision it links to has said **26%** since
  2026-08-23 — three months of the front page contradicting the document it
  points at;
* shards were said to be labelled `benchmark_candidate`, a legal label **no
  shard carries** — the registry reports `benchmark_review_candidate` and
  `governed_starter`, and `riskshard_modules.py list` prints the former;
* the IBM word counts were restated with no measurement date and no pointer to
  the audit record that owns them;
* and the worked decision's own inputs table published `frequency.min` as
  **0.10** for two days after the amendment eight lines above it said the value
  had moved to **0.0036**.

Every check here compares a document against the artifact that owns its number —
schema, registry, scenario, audit record, or another document. **None of them
pins a constant.** This repository has twice converted progress into a build
failure by asserting a counter's current value, and the lesson is not "don't
check documents", it is "check them against their owner". When the owner moves,
these fail, and the document is what has to change.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
WORKED = ROOT / "docs" / "WORKED_DECISION_AU_RANSOMWARE_LIMIT.md"
FINDINGS = ROOT / "docs" / "FINDINGS.md"
AU_SHARD = ROOT / "scenarios" / "au_finance_ransomware_midmarket.yaml"


def _money(text):
    """`AUD 2,310,000` / `0.0036` -> float."""
    cleaned = re.sub(r"[^\d.]", "", text.replace("**", ""))
    return float(cleaned)


class MeasurementVocabularyTests(unittest.TestCase):
    def test_the_readme_s_entry_count_matches_the_schema(self):
        import json

        schema = json.loads((ROOT / "schemas" / "evidence_record_schema.json").read_text())
        enum = (schema["properties"]["records"]["items"]["properties"]
                ["measurement_basis"]["enum"])
        claimed = re.search(r"(\d+)-entry measurement vocabulary", README.read_text())
        self.assertIsNotNone(claimed, "README no longer states the vocabulary size")
        self.assertEqual(
            int(claimed.group(1)), len(enum),
            f"README says {claimed.group(1)}-entry; the schema enum has {len(enum)}. "
            "ADR-0028 added the 19th and the README said 18 for two days.",
        )


class ExceedanceClaimTests(unittest.TestCase):
    """The front page quotes a figure from a document it links to."""

    def published_probability(self):
        row = re.search(r"^\|\s*20,000,000\s*\|\s*([\d.]+)%", WORKED.read_text(), re.MULTILINE)
        self.assertIsNotNone(row, "the worked decision's exceedance table lost its 20M row")
        return float(row.group(1))

    def test_every_readme_statement_of_it_rounds_to_the_table(self):
        claims = re.findall(r"AUD 20M from\s*\n?\s*0% to (\d+)%", README.read_text())
        self.assertTrue(claims, "README no longer states the 20M swap")
        expected = round(self.published_probability())
        for claimed in claims:
            self.assertEqual(
                int(claimed), expected,
                f"README says {claimed}%; the worked decision's table says "
                f"{self.published_probability()}%. It said 23% for three months.",
            )

    def test_the_readme_states_it_in_more_than_one_place(self):
        """Both instances went stale together, so both are checked."""
        self.assertEqual(len(re.findall(r"AUD 20M from\s*\n?\s*0% to \d+%",
                                        README.read_text())), 2)


class WorkedDecisionInputTests(unittest.TestCase):
    """The inputs table is the model's inputs; the scenario file is the model."""

    def test_every_anchor_in_the_table_matches_the_scenario(self):
        import yaml

        scenario = yaml.safe_load(AU_SHARD.read_text())
        rows = re.findall(r"^\|\s*`(frequency|impact)\.(min|likely|max)`\s*\|([^|]+)\|",
                          WORKED.read_text(), re.MULTILINE)
        self.assertEqual(len(rows), 6, "the inputs table lost a row")
        for family, anchor, value in rows:
            with self.subTest(parameter=f"{family}.{anchor}"):
                self.assertAlmostEqual(
                    _money(value), float(scenario[family][anchor]), places=4,
                    msg=(f"{family}.{anchor}: the table publishes {value.strip()}, the "
                         f"scenario holds {scenario[family][anchor]}"),
                )


class MaturityLabelTests(unittest.TestCase):
    def test_the_readme_only_names_rungs_a_shard_occupies(self):
        from engine.shard_registry import build_shard_registry

        live = set(build_shard_registry(ROOT)["maturity_counts"])
        paragraph = re.search(r"labeled by maturity:(.+?)benchmark-grade",
                              README.read_text(), re.DOTALL)
        self.assertIsNotNone(paragraph, "the Honest status paragraph changed shape")
        named = set(re.findall(r"`([a-z_]+)`", paragraph.group(1)))
        self.assertTrue(named, "no labels named")
        self.assertLessEqual(
            named, live,
            f"README names {sorted(named - live)}, which no shard carries. "
            f"The registry reports {sorted(live)}.",
        )


class IbmWordCountTests(unittest.TestCase):
    """A count this repository cannot regenerate still has an owner.

    Nothing here reads a PDF, so the counts cannot be produced on demand — but
    they are not loose either: `sources/audit.yaml` recorded them against the
    artifact's sha with a read date, and that record is the owner. These check
    that the prose agrees with it.
    """

    def audit_detail(self):
        import yaml

        rows = yaml.safe_load((ROOT / "sources" / "audit.yaml").read_text())["audit"]
        row = next(r for r in rows if r["source_id"] == "ibm_cost_data_breach_2026")
        return row, row["properties"]["distribution"]["detail"]

    def test_the_prose_counts_match_the_audit_record(self):
        _, detail = self.audit_detail()
        occurrences = re.search(r'"average" appears (\d+) times', detail)
        words = re.search(r"In ([\d,]+) words", detail)
        self.assertIsNotNone(occurrences)
        self.assertIsNotNone(words)
        readme, findings = README.read_text(), FINDINGS.read_text()
        self.assertIn(f'"average" {occurrences.group(1)} times', readme)
        self.assertIn(f'"average" {occurrences.group(1)} times', findings)
        self.assertIn(words.group(1), findings)

    def test_the_readme_carries_the_date_the_count_was_read(self):
        """Scoped to the claim's own sentence, and the first draft was not.

        Written as `assertIn(read_on, README.read_text())`, this passed a
        mutation that changed the date to 2026-11-12 — because the generated
        strength-ledger table further down the same file carries a
        `2026-08-16` row. A document-wide substring check is satisfied by any
        occurrence, which makes it a check on the document containing a date
        somewhere rather than on the claim carrying its own.
        """
        row, _ = self.audit_detail()
        read_on = str(row["properties"]["distribution"]["verified_on"])
        claim = self.readme_claim_sentence()
        self.assertIn(
            read_on, claim,
            "a number this repo cannot regenerate carries the date it was measured "
            f"(AGENTS.md). The audit read it on {read_on}; the claim says: {claim!r}",
        )

    def readme_claim_sentence(self):
        """The IBM claim and nothing else — bounded by the artifact id it names."""
        text = README.read_text()
        start = text.index('*Cost of a Data Breach* uses "average"')
        end = text.index("**The industry", start)
        return text[start:end]

    def test_the_readme_names_the_artifact_it_was_counted_in(self):
        row, _ = self.audit_detail()
        claim = self.readme_claim_sentence()
        self.assertIn(row["artifact_sha256"][:12], claim)
        self.assertIn(row["source_id"], claim)


if __name__ == "__main__":
    unittest.main()
