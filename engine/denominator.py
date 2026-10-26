"""The denominator question: when a report prints a percentage, of what?

ADR-0023. The audit asks four questions of every registered source — does it
publish a mode, a distribution, an exceedance statement, and who was measured.
None of them asks what a published percentage is a percentage **of**, and that
is the error this corpus most often catches other people making.

Sophos *State of Ransomware 2026* publishes *"just under half (48%) of payments
were $1 million or more"*. The denominator is organisations that **paid**, never
organisations attacked, and the audit record says so — in prose, inside the
answer to a different question. Quoted without that clause the sentence becomes
*"48% of ransomware attacks cost $1M+"*, which is a different and much larger
claim. The distance between those two readings is the whole of this module.

**The defect, measured before the field existed.** `population` (ADR-0003 asks
*who was measured*) is the nearest existing property and it does not answer this:
a report can describe its sample frame precisely and still print a percentage
over a sub-population of it. So the denominator is recorded **nowhere** — zero of
the audited records declare one — and where it survives at all it survives by
accident, in prose written to answer something else.

`coverage()` generates that premise rather than restating it, because the number
is the ADR's whole justification and a justification nobody can re-run is an
assertion. It reports three populations:

- **declared** — records carrying the ADR-0023 property. The field is the remedy,
  so this counts how far the remedy has got, and it starts at zero by definition.
- **incidental** — records whose existing prose mentions a denominator while
  answering one of the other four questions. Recoverable by a reader who already
  knows to look, which is not the reader this is for.
- **silent** — records where no denominator appears at all.

The split matters more than the total. A corpus that is *silent* needs reading;
one that is *incidental* needs only transcribing, and the two cost very different
amounts. Measuring that split before committing to 65 re-reads is the cheap half
of the work.

Nothing here parses a denominator out of prose and calls it data. The incidental
count is a **signal that prose exists**, deliberately not a value — scraping it
into a field would manufacture exactly the false precision the audit exists to
catch, and `incidental` is therefore a work estimate, never a source of record.
"""

import re

from engine.source_audit import load_audit

#: The four questions the audit already asks. ADR-0023 adds a fifth.
EXISTING_PROPERTIES = ("mode", "distribution", "exceedance", "population")

#: The property this module reads once ADR-0023 is implemented.
PROPERTY = "denominator"

#: What a denominator declaration may say, on the record's `base` field (ADR-0023).
#: Deliberately NOT `basis`, which already means how the answer was verified.
BASES = (
    "stated",          # the report names the base of its own percentage
    "derivable",       # the base is recoverable from figures the report prints
    "ambiguous",       # the report prints a percentage whose base it never fixes
    "not_applicable",  # the source publishes no percentage at all
)

#: One-line reading of each basis, for surfaces that show it to a reader.
BASIS_MEANING = {
    "stated": "the report names what its percentage is a percentage of",
    "derivable": "the base is not stated but can be recovered from figures the report prints, "
                 "and recovering it is the reader's work, not the publisher's",
    "ambiguous": "the report prints a percentage and never fixes its base — the most "
                 "misquotable shape there is",
    "not_applicable": "the source publishes no percentage, so there is no base to name",
}

#: Phrases that indicate a denominator was mentioned while answering another question.
#: A signal that prose exists. Never a value — see the module docstring.
_INCIDENTAL = (
    re.compile(r"\bn\s*=\s*[\d,]+", re.I),
    re.compile(r"\bdenominator\b", re.I),
    re.compile(r"\b(share|percentage|percent|%)\s+of\b", re.I),
    re.compile(r"\b(out of|of the)\s+[\d,]+", re.I),
    re.compile(r"\b(respondents|surveyed|sample of|base of)\b", re.I),
)


def _was_read(record):
    """A record is in scope once any property was verified against the artifact."""
    properties = record.get("properties") or {}
    return any(
        (prop or {}).get("basis") == "verified_against_artifact"
        for prop in properties.values()
    )


def _prose(record):
    """Every detail string on a record, joined — what a reader would have to scan."""
    properties = record.get("properties") or {}
    return " ".join(
        (properties.get(name) or {}).get("detail") or "" for name in EXISTING_PROPERTIES
    )


def mentions_a_denominator(record):
    """Does this record's prose mention a denominator while answering something else?

    A work estimate, not a reading. True means a transcriber has something to work
    from; it never means the corpus holds the value.
    """
    prose = _prose(record)
    return any(pattern.search(prose) for pattern in _INCIDENTAL)


def declares_a_denominator(record):
    """Does this record carry the ADR-0023 property?"""
    properties = record.get("properties") or {}
    declared = properties.get(PROPERTY) or {}
    return declared.get("basis") == "verified_against_artifact"


def coverage(root):
    """Generate ADR-0023's premise: how much of the read corpus records a denominator.

    Returns the three populations described in the module docstring, over the
    sources the audit has actually read. Unread sources are reported separately
    rather than folded in, because a source nobody could obtain is not evidence
    about a question nobody asked.
    """
    records = load_audit(root)
    read = [record for record in records if _was_read(record)]

    declared, incidental, silent = [], [], []
    for record in read:
        if declares_a_denominator(record):
            declared.append(record["source_id"])
        elif mentions_a_denominator(record):
            incidental.append(record["source_id"])
        else:
            silent.append(record["source_id"])

    return {
        "registered": len(records),
        "read": len(read),
        "unread": len(records) - len(read),
        "declared": len(declared),
        "incidental": len(incidental),
        "silent": len(silent),
        "declared_ids": sorted(declared),
        "incidental_ids": sorted(incidental),
        "silent_ids": sorted(silent),
    }


#: Signals that OUR OWN verified prose already pins the base hard enough that the
#: source is unlikely to repay a dedicated read. Deliberately narrower than
#: `_INCIDENTAL`, which only asks whether a denominator is mentioned at all.
_PINNED = (
    re.compile(r"\bn\s*=\s*[\d,]+", re.I),
    re.compile(r"\bdenominator\b", re.I),
    re.compile(r"\bbasis\s*:", re.I),
    re.compile(r"\b(among|of) (those|the organi[sz]ations|respondents|payers|victims)\b", re.I),
)


def screen(root):
    """Which sources are worth reading for their denominator, and which are not.

    ADR-0023's 2026-10-26 amendment drops the corpus-wide re-read. The property is
    kept for sources whose base is genuinely unclear, which turns the work from a
    queue into a screening problem — and screening is cheap in a way that reading
    is not.

    The screen reads **our own audit prose**, not the artifact. That is the point:
    those four answers are already a verified reading of the source by someone who
    opened it. If our own reading never once pins what a percentage is over, the
    source is a candidate for the fifth question. If it does, a dedicated read
    would mostly reproduce what the record already says.

    This nominates. It never records — a candidate still gets a real read before a
    value is written, and the ordering is not a finding.

    **Measured against the 15 sources of the first batch, which is the only ground
    truth there is: precision 30%, recall 100%.** It nominated 10 of the 15 and 7
    of those were already `stated`, so most nominations are a wasted read. It
    settled 5 and every one of them was genuinely `stated`, so nothing worth
    reading was dropped.

    That shape is the useful one and the numbers should be read as what they are.
    A conservative filter that cuts 65 sources to 38 with no measured miss is worth
    having; a precise instrument this is not, and 30% means roughly two in three
    nominated reads will confirm what the record already implied. The recall figure
    rests on 15 sources and should not be trusted as 100% — it means *no miss was
    observed*, over a sample too small to have observed a rare one.

    The false positives are instructive about why no prose screen can do better.
    `cyentia_iris_2022` is nominated and is the strongest `stated` in the batch —
    it names a denominator it cannot even obtain. Our four answers simply never
    quoted that part, because they were written to answer four other questions.
    The screen reads our prose, so it can only ever measure what our prose happened
    to mention.
    """
    records = [record for record in load_audit(root) if _was_read(record)]

    nominated, settled = [], []
    for record in records:
        source_id = record["source_id"]
        if declares_a_denominator(record):
            settled.append((source_id, "already declared"))
            continue
        prose = _prose(record)
        if any(pattern.search(prose) for pattern in _PINNED):
            settled.append((source_id, "base already pinned in our own prose"))
        elif mentions_a_denominator(record):
            nominated.append((source_id, "weak", 2))
        else:
            nominated.append((source_id, "silent", 1))

    # Silent first: a source our own four answers never touched on is the one most
    # likely to be hiding an unfixed base.
    nominated.sort(key=lambda row: (row[2], row[0]))
    return {
        "nominated": [(source_id, why) for source_id, why, _ in nominated],
        "settled": sorted(settled),
    }


def first_batch(root, size=15):
    """The sources ADR-0023's stop-and-look is measured on, chosen by rule.

    The failure condition — *if any single `base` holds more than 85% of the first
    15, retire rather than complete* — is only meaningful if the 15 are not chosen
    by whoever wants the answer. Fifteen industry surveys would almost all read
    `stated`; fifteen statutes would almost all read `not_applicable`. Either
    selection fires the condition on the sample rather than on the corpus.

    So the batch is **stratified by `source_type` and proportional to the read
    corpus**, and within each stratum the sources are taken in alphabetical id
    order. No judgement is exercised at any point, which is the property that
    makes the 85% test worth running at all. Largest strata are allocated first,
    with the remainder going to the largest types, so the 21 industry surveys
    carry about five seats and the long tail carries one each.
    """
    from engine.source_audit import load_registry

    registry = {entry.get("id"): entry for entry in load_registry(root)}
    read = [record for record in load_audit(root) if _was_read(record)]

    strata = {}
    for record in read:
        source_id = record["source_id"]
        kind = (registry.get(source_id) or {}).get("source_type") or "unknown"
        strata.setdefault(kind, []).append(source_id)
    for members in strata.values():
        members.sort()

    total = len(read)
    order = sorted(strata, key=lambda k: (-len(strata[k]), k))
    seats = {kind: (len(strata[kind]) * size) // total for kind in order}

    # Remainder to the largest strata, so rounding never silently empties the tail.
    while sum(seats.values()) < size:
        for kind in order:
            if seats[kind] < len(strata[kind]):
                seats[kind] += 1
                if sum(seats.values()) == size:
                    break

    batch = []
    for kind in order:
        batch.extend((kind, source_id) for source_id in strata[kind][: seats[kind]])
    return batch


def summary_line(root):
    """One line for the doctor, so the remedy's progress is visible every run."""
    result = coverage(root)
    return (
        f"{result['declared']} of {result['read']} read sources declare a denominator "
        f"({result['incidental']} mention one incidentally, {result['silent']} are silent)"
    )
