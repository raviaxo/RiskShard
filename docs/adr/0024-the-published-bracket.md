# ADR-0024 — A maximum is placed in a published distribution, not re-anchored onto one

- **Status:** **Accepted** (2026-11-12) — both declines accepted by the owner unchanged. *The
  Proposed status line said **three** declines and the Decision section carries **two**; decision 3
  records a limitation rather than declining anything. Corrected on acceptance and noted here rather
  than edited away, because a hand-written count in a status line is exactly the figure with no
  owner that AGENTS.md warns about.* Open questions 1 and 2 remain open and are **not** accepted
  here.
- **Date:** 2026-11-11
- **Deciders:** repo owner
- **Prompted by:** [Finding 12](../FINDINGS.md) — this repo's own source audit had recorded the
  exceedance denominator that ADR-0008, an engine docstring and finding 3 published as missing
- **Related:** [`0008-the-governed-tail.md`](0008-the-governed-tail.md) (this corrects its
  premise and keeps its vocabulary), [`0007-construct-coherence.md`](0007-construct-coherence.md)
  (the all-cause/threat-specific question), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (the test that decides declines 1 and 2)

## Context

[ADR-0008](0008-the-governed-tail.md) gave a maximum a third declared axis — *what, if anything,
is known about being exceeded* — and recorded that the portfolio could mostly answer only
`none_known`. The reason it gave was scarcity. `engine/exceedance.py` told readers that published
loss distributions with tail quantiles are *"rare and mostly commercial"*, and
[finding 3](../FINDINGS.md) closed by saying we had not found one *"publicly, anywhere."*

**The premise was fair when written and was never revised.** ADR-0008 is dated 2026-08-07 and
finding 3 was derived 2026-08-13. Cyentia's IRIS 2025 — which publishes 50th and 95th percentile
losses by revenue tier in its Table 1 — entered the corpus on **2026-08-15**, eight days and two
days later respectively.

**It did not sit unread.** `sources/audit.yaml` records `cyentia_iris_2025` as
`verified_against_artifact` against the report that same day, and the `exceedance` property quotes
it: *"The typical (median) incident costs about $600K, while more extreme (95th percentile) losses
swell to $32 million."* The audit calls it the most complete distribution in the corpus.

The evidence record anchoring `impact.max` on that source tells the opposite story. Extracted
2026-06-03 from the publisher's 4,113-character summary page — two months before the report was
obtained — it carries `exceedance_basis: none_known` and a `limitations` line reading *"not a
formal percentile for this scenario."*

**So the defect is not a missed number. It is that two governed surfaces in this repository held
contradictory answers about the same figure for 88 days, and nothing compared them.** ADR-0015 and
[ADR-0016](0016-the-audit-is-the-product.md) made the audit the product; no path routes an audit
answer back to the evidence records citing that source, and a finding published the absence of a
denominator the audit had already written down. `docs/internal/NEXT_STEPS.md` recorded this on 2026-10-27 as the **eighth** time
a source recorded as owed turned out to be held, and that count is as of that date.

**But it is a different class from the other seven, and the difference matters.**
`engine.intake.blocked_but_held` exists to fail the doctor on that pattern — it finds sources the
audit calls unreadable for which a candidate document is nevertheless on disk. It cannot catch this
one, and no stretch of it would. `cyentia_iris_2025` is not blocked, not missing and not unread:
it is registered, held, and **verified against the report on all four audit properties.**

*We said we lacked a source and did not* is a check we have. **The check we do not have is whether
what the audit learned ever reached the records that cite the same source** — or the findings that
reason about it. The audit is a per-source surface and the evidence records are a per-parameter
surface, and nothing in the repo reads one against the other.

## Decision

**A shard's maximum is placed against the published distribution for its own org profile's revenue
tier, and nothing is re-anchored.** `engine/tail_bracket.py` computes it; the numbers live in a
committed verbatim extract of the source table and nowhere else, so prose cannot drift from them.

Three things follow, and two of them are declines.

### 1. The bracket is reported, and it is not a new `exceedance_basis` value

A bracket says *this value sits below (or above) the published 95th percentile for its tier*. That
is weaker than `modeled_quantile`, which ADR-0008 defines as **a stated percentile** of a published
distribution. We do not know the anchor's percentile; we know which side of one point it falls on.

Minting a fifth vocabulary value for it is **declined** under [ADR-0009](0009-what-riskshard-is-and-is-not.md):
it makes the method more sophisticated without making any published number more correct. The
exceedance ladder stays a claim ladder. The bracket is reported as a finding and, when the next
increment lands, as a caveat on the record — not as a rung.

### 2. No anchor moves onto the IRIS figure

Swapping a documented-event maximum for the tier's 95th percentile would buy a stated quantile and
**pay for it in provenance** — exactly the trade ADR-0008 refused in the other direction when it
declined to swap `us_finance_data_breach_midmarket`'s `observed_rank` maximum for a registry entry.

It is also worse than neutral in at least one case. `au_finance_ransomware_midmarket` anchors on
Latitude's disclosed AUD 76M; the tier 95th is USD 9.1M. The swap would move a published maximum
**down by a factor of six**, replacing a real Australian financial-services loss with an all-cause
global percentile. **Declined.**

### 3. The denominator under a `modeled_quantile` is now visible, and it is narrower than it reads

The portfolio's only two quantified maxima — DE and JP manufacturing — both sit at **0.41×** their
tier's 95th percentile. Their $5M threshold is at the 82nd percentile *of ransom payments made by
organisations that paid*, a self-selected denominator. Against all-cause loss for a firm of their
size it is unremarkable.

Both statements are true and they are not the same instrument. ADR-0008's vocabulary records *what
kind* of exceedance statement a record carries; it does not record **what population the statement
is over**, and until now nothing in the repo could tell a reader that two `modeled_quantile`
records might be answering about different worlds. Recorded here as a live limitation of the axis,
not fixed here.

## Scope

**Decided here:** the placement, the two declines, and the correction of ADR-0008's premise.

**Built 2026-11-11:** `engine/tail_bracket.py`, the committed source extract at
`extractions/cyentia_iris_2025_table1_loss_percentiles.txt`, `tests/test_tail_bracket.py`
(13 tests, the prose check verified to fail on a one-digit drift), finding 12, withdrawn claim 3,
and the correction to `engine/exceedance.py`'s docstring.

**Deliberately not built here, and owed:** the bracket does not yet appear on any record or any
reader-facing surface. The five maxima it most concerns still carry `limitations` text written
before the distribution was found. That is a `evidence/` change, which moves the data-pack
fingerprint and takes its own PR — see open question 1.

✅ **Built 2026-11-14, three days later.** All five `none_known` maxima now carry the placement in
their `limitations`, generated from `engine/tail_bracket.py` rather than typed, and pinned by
`tests/test_placed_maxima.py` — which asserts the p95, the converted USD value, the ratio and the
meaning sentence against the live engine on every run, and was verified to fail on all five when
the p95 is moved by one dollar. **Three of the five sit below their tier's 95th percentile**
(0.21×, 0.70×, 0.73×), so the caveat tells a reader that the figure they are treating as an outer
bound is one the population exceeds more than 5% of the time. No `exceedance_basis` changed, no
anchor moved, and no fifth rung was minted — the two declines above are asserted by that same test
file rather than left to good intentions. The data-pack fingerprint moved `749540a5b1f6` →
`f9c2befadfbe`; the strength ledger records at release and reads `needs_review` until one is cut,
which is the documented normal state of an unreleased pack change.

⚠️ **Open question 1 is partly answered by construction, and that was not noticed until the test
suite said so.** `limitations` is rendered into [`docs/EVIDENCE_REPORT.md`](../EVIDENCE_REPORT.md),
which is published — so writing the placement onto the record *put it in front of readers in the
same commit*, and `tests/test_evidence_report_is_current.py` failed until the report was
regenerated. The ADR-0007 risk open question 1 was weighing is therefore live now, not deferred.
Two things make it acceptable rather than accidental: the caveat names itself as an all-cause
distribution placed against a threat-specific anchor, in those words and asserted by a test; and a
caveat that a maximum is routinely exceeded is of no use to the one reader who most needs it if it
is held back pending a display decision.

**What remains genuinely undecided** is narrower than the question as written — whether the bracket
becomes a *displayed field* on the explorer, beside the value, rather than prose inside a caveat.
That is the version ADR-0007 argues about, and it is not decided here.

*Recorded this way because the alternative was to regenerate a published report and say nothing. An
open question answered as a side effect is still answered, and the ADR has to say which half went.*

## Open questions

1. **Does the bracket reach the reader, or stay a finding?** The honest case for putting it on the
   explorer and the evidence report is that a reader treating a maximum as an outer bound is
   exactly the reader who needs to know the population routinely exceeds it. The case against is
   that an all-cause distribution sitting beside a threat-specific anchor invites precisely the
   construct confusion [ADR-0007](0007-construct-coherence.md) exists to prevent. **Not decided.**

2. **Should the axis record its denominator?** Decision 3 shows two `modeled_quantile` records
   making statements over different populations with nothing distinguishing them. A fix is a new
   field, which is a new declared axis, which AGENTS.md permits only from a defect measured in our
   own data. This *is* such a defect — it is measured above. Recorded as a candidate, not opened.

3. **How much of the corpus was read off the wrong artifact?** Not opened by this ADR, but
   **sized** by it, because an unsized question gets deferred forever.

   *Measured 2026-11-11, by hand — this count is not yet generated by anything:* the corpus holds
   **129 artifacts across 122 stems**, and **6 stems hold both a web page and a PDF of the same
   source** — the three Cyentia IRIS reports, Interos 2022, NetDiligence 2025 and Ponemon/DTEX 2023.
   **21 evidence records draw on those six. 9 of the 21 cite the summary or press page rather than
   the report, and all 9 are Cyentia.**

   So the pattern finding 12 caught is not a one-off; it is nine records, of which this ADR re-reads
   the properties behind one. The other eight have not been checked against their reports.

   **The check that would own this number does not exist yet** and is the obvious candidate: flag
   any evidence record whose source has a richer artifact on disk than the one its extraction cites.
   `engine.intake.blocked_but_held` is the near neighbour and cannot see it, for the reason given in
   *Context*.

   ⚠️ **BUILT 2026-11-14 as `engine/artifact_fit.py`, and it corrects the hand count above — in
   the direction that makes the problem bigger.** The sentence *"9 of the 21 cite the summary or
   press page rather than the report, and all 9 are Cyentia"* is **wrong on both halves**:

   | | hand-counted 2026-11-11 | generated 2026-11-14 |
   | --- | --- | --- |
   | records citing something other than the report we hold | 9 | **26** |
   | …of which Cyentia | 9 (all) | 14 |
   | …of which **not** Cyentia | 0 | **12** — five NetDiligence, four Sophos, two Ponemon/DTEX, one IBM |
   | sources affected | 1 publisher | **7 sources across 5 publishers** |

   *The generated figures were themselves corrected once before this table settled, and the
   correction is the more useful half.* The first build grouped the files in `sources/raw/` and
   looked for stems holding both a page and a report. It found **21** records on the maintainer's
   machine and **zero in CI** — `sources/raw/` holds large third-party PDFs and is deliberately not
   distributed, so the check read an empty directory and reported a clean corpus. A check that
   reports zero on every clone but one publishes reassurance, which is worse than reporting
   nothing. Asking the manifest instead is portable **and** a better question: the disk version
   could only flag a source whose page we also happened to archive, which is an accident of
   collection rather than a property of the defect. That is how four more Sophos, IBM and
   NetDiligence records came into view.

   The original text is left standing above rather than edited, because **this is the ADR's own
   argument landing on the ADR itself.** It flagged the count as *"not yet generated by anything"*
   and that is precisely why it was wrong — a number typed into prose has no owner and nothing
   watching it. `tests/test_artifact_fit.py` is the owner now, and the doctor prints the
   population every run.

   *Two further populations the hand count could not see, and that collapsing them is how it went
   wrong:* **28** records cite something other than the stored artifact (the wider set — often
   benign, since a landing page is a fair permalink), and **21** records have a `source_id` with no
   manifest entry at all, so they are **unmeasured rather than clean**.

   **What is still owed:** the 26 flagged records have not been re-read against their reports. One
   of them produced the contradiction this ADR is named for; the other twenty-five have never been
   checked, and the population is nearly three times what was planned for. It is not only
   bookkeeping — `sophos_manufacturing_ransomware_extreme_case_threshold_usd_2025` is in the list,
   and it is the anchor behind the DE and JP `modeled_quantile` maxima that decision 3 above
   reasons about.
