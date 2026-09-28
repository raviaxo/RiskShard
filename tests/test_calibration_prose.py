"""A calibration's summary prose names the edition its anchors actually stand on.

Every calibration profile opens with a `metadata.notes` block that tells a reader, in
one paragraph, what the six parameters rest on. That paragraph is prose, so nothing
generated it and nothing was watching it. On 2026-08-23 the Australian ransomware
impact anchor moved one edition forward — Sophos Australia 2025 to Sophos Australia
2026, USD 650,000 to USD 1,660,000, a 2.55x move that shifted the published figure by
7.4%. Fourteen tests fired on that value and every per-parameter `rationale` was
rewritten. The notes block above them was not, and went on saying `impact likely is the
Australian mean recovery cost from the Sophos Australia 2025 country cut` for the next
five weeks, through two releases and a QA pass that read the roadmap, the links, the
dashboard and the registry.

That is the failure mode AGENTS.md names: a fact typed into prose has no owner and
nothing watching it. The edition an anchor stands on is owned by the evidence record and
its source registry entry, so this check reads the paragraph and holds it to them.

**Per-parameter `rationale` strings are deliberately not checked.** A rationale is
expected to name the anchor it *replaced*, which means naming an edition the calibration
no longer binds: `sg_finance_bec.yaml` frequency.max records that it replaces `the US AFP
2026 payments-fraud prevalence (0.74)` while binding a CSA Singapore record. That is
AGENTS.md's "caveats get louder, not quieter" working as intended, and a check that fired
on it would be a check worth suppressing. The notes block is different in kind: it
describes what the calibration rests on *now*.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

#: A four-digit year, matched inside snake_case ids too — `\b` does not fire between
#: `_` and a digit, because `_` is itself a word character.
YEAR = re.compile(r"(?<![0-9])(20[12][0-9])(?![0-9])")

#: How far after a publisher's name a year is still taken to be that publisher's edition.
WINDOW = 90

#: Carries conversion rates, not parameter anchors.
NOT_A_PROFILE = {"fx_rates.yaml"}


def registered_sources():
    doc = yaml.safe_load((ROOT / "sources" / "registry.yaml").read_text()) or {}
    return {s["id"]: s for s in (doc.get("sources") or []) if s.get("id")}


def evidence_records():
    out = {}
    for path in sorted((ROOT / "evidence").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for record in doc.get("records") or []:
            out[record["id"]] = record
    return out


def edition_years(source_id, source):
    """The year(s) this edition is known by: its id, then its publication date."""
    years = set(YEAR.findall(source_id))
    if not years:
        years = set(YEAR.findall(str(source.get("publication_date", ""))))
    return years


def calibration_profiles():
    return sorted(
        p for p in (ROOT / "calibrations").glob("*.yaml")
        if p.name not in NOT_A_PROFILE
    )


class CalibrationProseTests(unittest.TestCase):
    def test_notes_do_not_name_an_edition_the_calibration_does_not_bind(self):
        sources = registered_sources()
        records = evidence_records()

        #: Every edition year each publisher has registered, so that a bare year near a
        #: publisher's name is only read as an edition when one exists.
        published_years = {}
        for source_id, source in sources.items():
            publisher = (source.get("publisher") or "").strip()
            if publisher:
                published_years.setdefault(publisher, set()).update(
                    edition_years(source_id, source)
                )

        stale = []
        for path in calibration_profiles():
            profile = yaml.safe_load(path.read_text()) or {}
            notes = (profile.get("metadata") or {}).get("notes") or ""
            if not notes:
                continue

            bound_years = {}
            for group, slots in (profile.get("parameters") or {}).items():
                for slot, spec in (slots or {}).items():
                    record = records.get((spec or {}).get("evidence_id") or "")
                    if not record:
                        continue
                    source_id = str(record.get("source_id") or "")
                    source = sources.get(source_id)
                    if not source:
                        continue
                    publisher = (source.get("publisher") or "").strip()
                    if publisher:
                        bound_years.setdefault(publisher, set()).update(
                            edition_years(source_id, source)
                        )

            haystack = notes.lower()
            for publisher, bound in bound_years.items():
                if not bound:
                    continue
                for match in re.finditer(re.escape(publisher.lower()), haystack):
                    window = haystack[match.start(): match.start() + WINDOW]
                    for year in YEAR.findall(window):
                        if year in bound:
                            continue
                        if year not in published_years.get(publisher, set()):
                            continue  # a date, not one of this publisher's editions
                        stale.append(
                            f"{path.name}: metadata.notes names {publisher} {year}, "
                            f"but the {publisher} edition(s) this calibration binds "
                            f"are {sorted(bound)}"
                        )

        self.assertEqual(
            [], stale,
            "Calibration summary prose names an edition its anchors no longer stand on:\n"
            + "\n".join(stale),
        )


if __name__ == "__main__":
    unittest.main()
