# M4 runbook — the release that measures the kill criterion

*Written 2026-10-26, six days before it can be run. The point of writing it now is that
nothing about the outcome gets decided on the day.*

**Do not run this before 2026-11-01.** [ADR-0017](../adr/0017-the-kill-criterion-gets-a-clock.md)
section 2 sets the measurement at *the first release on or after* that date, and section 3 says in
writing that the date does not move again. A release cut on 2026-10-31 either misses the trigger or
moves the date, and the credibility of the whole exercise rests on it not having moved. Six days of
waiting is the cheapest thing this project will ever buy.

## What is already decided, so that nothing is decided on the day

| question | answered by | answer |
| --- | --- | --- |
| What are the two metrics? | ADR-0012 decision 5 | shards whose `impact.max` cites a registry entry; entries contributed from outside |
| Does the criterion move? | ADR-0017 §3 | No. One amendment was allowed and ADR-0022 was explicitly not it |
| What if a metric is uninformative? | ADR-0017 §4 | Grounds for retiring, **not** for extending |
| What shape does retirement take? | ADR-0017, Alternatives | *"Retire the trial but keep the 36 events as a published dataset with no claim on the shards"* |
| What happens to the census? | same sentence; ADR-0017 OQ1 | The 36 events survive; the EDGAR census stands as [Finding 8](../FINDINGS.md) regardless |
| Why does metric 1 read zero? | `citation_candidates()`, ADR-0022 amendment | Population mismatch, not neglect — 10 of 11 shards have no country-and-threat match, the 11th is blocked because citing would trade `observed_rank` for provenance |
| Why does metric 2 read zero? | ADR-0022 OQ1, closed 2026-10-22 | No route was offered, deliberately, because the only route that would help solicits the slice ADR-0012 forbids |

**The one thing not decided: the measured numbers.** They are generated on the day by running the
tool, and they go into the ADR from that output. Both have read zero every time they have been run,
and nothing between now and then can change either — no shard can begin citing an entry without a
parameter change, and no contribution route exists. But *expected* is not *measured*, and the
difference is the entire reason ADR-0022 built the meter.

## Order of operations

Cutting a release and archiving it are two steps, and on 2026-09-27 only the first had a check —
which is how `v0.12.0` shipped with a 404 on its own pinned citation. Follow the order.

### 1 · Measure first, before anything is cut

```bash
source .venv/bin/activate
python -c "from engine.loss_events import trial_metrics; from pathlib import Path; \
import json; print(json.dumps(trial_metrics(Path('.')), indent=2))"
python scripts/riskshard_doctor.py            # the loss-event line prints both counts
```

Record the output verbatim. This is the measurement, and it is taken **before** the release so that
the release cannot be accused of having been shaped by it.

### 2 · Write ADR-0024 from that output

The outcome ADR. Not pre-written, because writing a conclusion before its measurement is the move
this whole criterion exists to refuse — but everything *except* the numbers is settled in the table
above, so it is assembly rather than deliberation.

It must say, in these terms: **the registry was built on a corpus that structurally cannot serve
the grid it was meant to serve, and was forbidden from growing into a shape that could.** That
sentence is already drafted into ADR-0022's open-question closure and should be carried across
rather than rewritten. Both zeros are true; neither is about adoption; and ADR-0017 §4 pre-decided
that this retires the registry rather than extending it.

### 3 · Retire the trial, keep the data

Per ADR-0017's pre-specified shape. The 36 events stay as a published dataset with **no claim on
the shards**. Nothing is deleted — citations may pin it.

- `loss_events/` keeps its records and its README gains the retirement notice
- `engine/loss_events.py` keeps `trial_metrics` as the record of the result
- the doctor's loss-event check becomes a retirement record rather than a live criterion
- `schemas/loss_event_schema.json` keeps the `contribution` block; it is vestigial and saying so is
  cheaper than a migration

### 4 · Reconcile the owner docs

ADR-0005, ADR-0012, ADR-0017, ADR-0022 · `docs/ROADMAP.md` M4 and M5 · `loss_events/README.md` ·
`CHANGELOG.md` · `docs/internal/NEXT_STEPS.md`.

### 5 · Cut the release — every step, in order

```bash
python scripts/build_audit_page.py --check     # these three fail if a generated page is stale
python scripts/build_reports.py --check
python scripts/build_social_card.py --check
python -m unittest discover -s tests           # test_evidence_report_is_current and
python scripts/validate_evidence.py            # test_readme_progress_is_current are in here
python scripts/contributor_preflight.py
python scripts/strength_ledger.py record       # clears the ledger's needs_review
python scripts/strength_ledger.py markdown     # regenerates the README table
python scripts/build_explorer.py
python scripts/build_explorer.py --archive     # ← THE STEP THAT WAS SKIPPED ON v0.12.0
python scripts/riskshard_doctor.py             # must read pass on all 18
```

Then tag **the merge commit**, not the branch head, and cut the GitHub release.

### 6 · Verify the citation resolves, by fetching it

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://raviaxo.github.io/RiskShard/r/<release>/
```

A 200, not an assumption. `tests/test_release_archives.py` and the doctor's `release archives`
check both assert the archive exists, and neither can tell you the page is actually being served.
The v0.12.0 404 was found by fetching the link before handing it over.

**If the archive must be rebuilt, build it from a worktree at the tag, never from HEAD.**
`build_explorer.py` reads the working tree, so archiving from a HEAD that has moved past the tag
produces a file labelled with one release and containing another. A wrong archive is worse than a
missing one, because the missing one 404s honestly.

## What does not happen on this release

- **No parameter value moves.** This is a governance release.
- **The criterion is not re-litigated.** ADR-0017 §4 settled the uninformative-metric case in
  advance precisely so that the day of the measurement is not the day of the argument.
- **It is not published as the headline.** Owner's steer, 2026-10-22: the claim is an improvement
  shipped on a good product, not a confession. The measurement is recorded, the ADR is written, the
  release goes out. It does not become a LinkedIn post.

## Known state going in, as of 2026-10-26

- `main` is green: 534 tests, evidence clean, preflight clean
- the doctor reads `needs_review` on **one** line — the strength ledger, because the ADR-0023
  schema change moved the pack fingerprint to `239237c338a4`. This is the documented normal state
  of an unreleased pack change and **step 5 clears it**
- `v0.13.0` is the current release and its archive resolves
- open branch: `shard/denominator-adr`, which should be merged or closed before the release so the
  tag lands on a clean `main`
