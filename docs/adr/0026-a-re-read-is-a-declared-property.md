# ADR-0026 — A re-read is a declared property, pinned to the artifact's hash

- **Status:** Accepted (2026-11-20) — decided by the owner after the first re-read ran and the
  count did not move
- **Date:** 2026-11-20
- **Deciders:** repo owner
- **Extends:** [`0023-the-denominator-is-a-declared-property.md`](0023-the-denominator-is-a-declared-property.md)
  (same shape, one level out: a fact we keep asserting in prose becomes a field)
- **Related:** [`0024-the-published-bracket.md`](0024-the-published-bracket.md) (the defect that
  started the campaign), [`0015-the-source-audit.md`](0015-the-source-audit.md) (mechanical
  staleness detection by artifact hash), [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md)
  (part 1's finite-table test, applied below)

## Context

`engine/artifact_fit.py` flags **26 evidence records across 7 sources** that cite something other
than the report we hold. On 2026-11-20 the first of them was re-read against the publisher's file:
`sophos_state_ransomware_manufacturing_2025`, the anchor behind both `modeled_quantile` maxima in
the portfolio. The re-read found a real defect — the 82nd-percentile claim rests on `n=67`, about
twelve organizations, and the record did not say so — and the corrections shipped.

**The count stayed at 26.**

That is correct behaviour and it is also the problem. The check asks *does this record cite the
report we hold*, and the answer is still no: the record cites the publisher's dated blog permalink,
which is the right thing for a reader to be sent to. Nothing anywhere records that a human opened
the report and compared them. Re-read all 26 and the number still reads 26, so **the one figure
that would show the work is structurally incapable of moving.**

The fact had a home in the first re-read: a sentence in `extraction_notes`. That is prose. It has
no owner, nothing counts it, and a rewording breaks it silently — the exact failure this repository
has now hit four times with hand-written figures.

## Decision

**A re-read is recorded on the record, in two fields, and the verification is pinned to the bytes
that were read.**

```yaml
artifact_verified_at: "2026-11-20"
artifact_verified_sha256: c579c711f3004db660c547e4c73be6b0e4997cb5b76fffacabebacf928f99eae
```

### 1. The hash is the load-bearing half

`sources/manifest.json` already stores a `sha256` per source. Recording the hash that was actually
read means the verification **expires itself**: when a publisher reissues the file, the manifest
hash changes, the two stop matching, and the record silently drops back to unverified with the
doctor saying so. A date alone would keep asserting that we checked a document that no longer
exists.

This is [ADR-0015](0015-the-source-audit.md)'s mechanical staleness detection applied one level
down — from "has this source changed" to "is our reading of it still a reading of this file."

### 2. It reports, it does not gate

A mismatch between the stored hash and the recorded one is a **warning**, never an error. The
honest meaning is *this needs looking at again*, not *this is wrong*. Malformed input — one field
without the other, a hash that is not 64 hex characters, a date that is not a date — is an error,
because that is a typo rather than a finding.

### 3. Both fields are optional, and absence means "nobody has checked"

Not "clean". The 21 records with no manifest entry already taught this distinction, and
`fit_report` already returns `None` rather than `0` where it has not looked.

## Consequences

- **The campaign becomes countable.** `artifact fit` splits the 26 into verified, stale and
  unverified, and the doctor line moves as records are read.
- **A publishable claim comes out of it**, which is the point under the 2026-10-22 steer: *26
  anchors re-read against the publisher's own file, each pinned to that file's hash, so a reissue
  un-verifies it automatically.* That is a product property, not a confession.
- **Two more fields on the evidence schema.** Both optional; the 17 required fields are untouched.
- **The four Sophos records are backfilled in the same change**, so the first verified count is 4
  rather than 0 and the new line is exercised by real data on its first run.

## Alternatives considered

- **Repoint `source_url_or_citation` at the report.** Makes the flag disappear, and that is the
  objection: the flag would disappear without anyone having read anything. It also trades a dated
  permalink a reader can open for a landing page — the Sophos stored artifact URL is not even a
  PDF — and it conflates *where a reader finds this* with *what we read*. Two facts, two homes.
- **Parse the re-read date out of `extraction_notes`.** Cheapest and rejected for the reason the
  decision exists: prose has no owner.
- **Build nothing and keep re-reading.** Genuinely considered, because the owner's standing
  objection is that this project spends too much of itself auditing itself. Rejected because the
  alternative is worse on exactly that axis: twenty-five more re-reads with nothing to show for
  them is the most demoralising available version of the complaint.

## Why this clears the scope gates

It does **not** make a published number more correct, so it fails
[ADR-0009](0009-what-riskshard-is-and-is-not.md)'s first test and must stand elsewhere. It does:

- **AGENTS.md's bar for new machinery** — the defect is measured in our own data rather than
  suggested from outside. The campaign ran once, and the count did not move.
- **[ADR-0016](0016-the-audit-is-the-product.md) part 1** — *does this add a row to a finite table,
  or a parameter to an infinite one?* It adds a **column to a finite and shrinking table**: 26 rows,
  fewer after each re-read. That is the permitted shape.

Recorded explicitly because "it is obviously useful" is how an infinite surface gets born.

## Open questions

1. **Does a verified record keep its page citation?** This ADR assumes yes — the permalink serves
   the reader, the hash serves the audit. Not revisited unless a reader complains.
2. **Should the audit surface carry the same field?** `sources/audit.yaml` records readings per
   source and has the same rot risk. Out of scope here; this ADR governs evidence records only.
