# ADR-0003 — Shared, named impact bridges

- **Status:** Accepted (2026-07-31) — **parts 1 and 2 only**
- **Date:** 2026-07-28
- **Deciders:** repo owner
- **Scope accepted:** declare the population mismatch on each record (part 1) and report
  cell-matched and bridged counts separately (part 2). Parts 3 and 4 (shared bridge objects,
  documented transfer rules) are **not** accepted and stay available if something forces them.
- **Deciding evidence:** on 2026-07-30 the strength ledger recorded the Australian impact
  reselect — a swap from IBM's UK enterprise-weighted benchmark to its global average, moving
  that shard's AVG roughly fiftyfold — as `66/66 -> 66/66`, a zero delta. The headline metric
  cannot see evidence quality change, which is the defect this ADR fixes.
- **Related:** [`../internal/coverage_harvest.md`](../internal/coverage_harvest.md),
  [`../internal/dora_prescout.md`](../internal/dora_prescout.md),
  [`../internal/es_availability_prescout.md`](../internal/es_availability_prescout.md),
  [`../METHODOLOGY.md`](../METHODOLOGY.md) (frequency/severity asymmetry)

## Context

Frequency evidence has become abundant. Eurostat `isoc_cisce_ic` carries country- and
size-specific incident rates for **35 countries**; DORA supplies a supervisory per-entity
rate for the EU financial sector. Neither existed in the repo a week ago.

Impact has gone the other way. Two independent scouting passes on 2026-07-28 both dead-ended:

- **Spanish national and regional bodies** (INCIBE, AEPD, Catalonia's agency, BCSC)
  publish incident **counts and typologies, essentially never euros**. AEPD publishes
  euros, but they are regulatory penalties, not event losses.
- **DORA mandates cost reporting** under Article 22(2) — and the first report found that
  half of major incidents reported no cost or under EUR 1,000, with a further 15% leaving
  the field blank, which the ESAs themselves flag as probable mis-reporting.

This is not bad luck. Per-country, per-sector, per-size loss-magnitude data mostly **does
not exist in public sources**, and there is no reason to expect it to appear. The engine
already says as much in `IMPACT_UNCERTAINTY_NOTE`: severity is far less predictable from a
shard's cell than frequency is.

### What the impact sides actually look like (measured 2026-07-29)

An earlier draft of this ADR asserted that "several impact sides are the same generic
cross-cyber research re-cited per shard." **That was overstated, and the measurement is
recorded here rather than quietly dropped.**

Across the 33 impact parameters in the 11 shards, most are country- or sector-matched:
Bitkom for Germany, Asteres and the IBM France release for France, DSIT and the FCA for
the UK, the NPA for Japan, ACCC and Business Queensland for Australia, SPF for Singapore,
NetDiligence and Coalition for the US. Only **three** use Cyentia.

The genuine cross-cell reuse is a **minority, and it is concentrated**:

| shard | parameter | source population | mismatch |
|---|---|---|---|
| `sg_finance_bec` | impact.likely | FBI IC3 (US complaints) | country |
| `sg_finance_bec` | impact.min | Verizon DBIR (global/US) | country |
| `au_finance_bec` | impact.likely | FBI IC3 (US complaints) | country |
| `ca_finance_data_breach` | impact.min, impact.max | Cyentia IRIS (cross-cyber, global) | country + threat |
| `au_finance_ransomware` | impact.max | Cyentia IRIS (cross-cyber, global) | threat |
| `de_industrial` / `jp_manufacturing` | impact.likely, impact.max | Sophos manufacturing (global survey) | country only — sector matches |

So roughly six clear cross-country bridges plus one global sector survey serving two
countries — call it a fifth to a third of the impact side, concentrated in **Singapore and
Canada**, not a portfolio-wide condition.

## Problem

**Bridging is currently undetectable programmatically.** An attempt to classify these
records automatically by scanning caveat text flagged 26 of 33 — because a well-written
caveat *always* qualifies its population ("not mid-market-specific", "not
financial-services-specific"). Honest caveats and borrowed sources are textually
indistinguishable, so nothing in the coverage tooling can tell the difference between a
parameter backed by its own country's statistics and one borrowed from another country.

That is the real defect, and it is smaller and sharper than the earlier framing: the repo
reports **66/66 source-backed** with no way to say how many of those 66 are backed by
evidence drawn from the shard's own cell. A reader counting 66/66 reasonably infers more
cell-specific evidence than exists, and the tooling cannot correct them because it does not
know either.

Caveat dilution is a secondary concern: repeating a near-identical limitation across
several records means the fourth restatement gets skimmed. It matters more as shard count
grows, which the new frequency supply now permits.

## Proposal

Scoped down from the earlier draft, in line with what the measurement shows.

**1. Mark the mismatch explicitly.** Every evidence record gains a declared relationship
between the source's population and the shard's cell — matched, or bridged on country /
sector / threat / size, naming which. This is the load-bearing change: it makes bridging
*detectable*, which caveat prose cannot.

**2. Coverage reports both numbers.** Not one headline, but "N cell-matched, M bridged" —
so `params_source_backed` stops implying specificity it cannot verify, and the strength
ledger can show bridged counts falling as evidence improves.

**3. Where the same source legitimately serves several shards, declare it once.** Sophos
manufacturing serving both DE and JP is a *correct* reuse — same sector, same threat, a
global survey by design. Declaring it as one named bridge with one carefully written
limitation, referenced twice, is more honest than two near-identical records and makes the
shared dependency visible.

**4. Transfer rules where a bridge crosses country or size.** Loss magnitude scales with
revenue, and sources such as NetDiligence publish severity by revenue band. A documented,
sourced scaling function is a defensible way to move one strong source across cells;
silent reuse is not.

### Consequences, including the uncomfortable one

**The headline number will fall — by a known, modest amount.** "66/66 source-backed"
becomes roughly "**59–60 cell-matched + 6–7 bridged**" on the measurement above. That is
the point: a metric that cannot fall is not a measurement, and the ledger currently cannot
distinguish more evidence from evidence borrowed across a border.

**It makes the weakness locatable.** Today a reader cannot tell which shards are weak on
impact. Afterwards it is obvious that **Singapore and Canada** carry the borrowed evidence
— which is also a work queue, since those are exactly the two shards to fix first.

**It makes correlation visible.** Where several shards lean on the same study, their loss
figures are not independent. Nothing surfaces that today, and it matters to anyone
aggregating across shards.

**It lowers the cost of a real improvement.** Replacing one declared bridge upgrades every
shard referencing it, rather than requiring separate edits per shard.

**It is a schema change**, so it needs a migration for existing records and touches the
coverage tooling, `provenance`, the evidence report and the explorer. That is real work for
a change that adds no new evidence — the honest counter-argument to adopting it now rather
than after the CA/AU impact upgrades, which may retire two of the six bridges anyway.

## Alternatives considered

- **Do nothing.** Defensible: every individual record is already honest and caveated.
  Rejected because the aggregate claim drifts further from reality with every shard added,
  and the frequency supply now makes rapid addition easy.
- **Stop adding shards until per-cell impact data exists.** Rejected: the scouting says
  that data largely does not exist, so this is a permanent freeze on coverage.
- **Keep per-shard records but tag them as bridged.** A lighter version of this proposal
  and a reasonable fallback — it fixes the counting problem without the schema change,
  but leaves the caveat duplicated and the correlation invisible.

## Recommendation

**Adopt parts 1 and 2 (mark the mismatch, report both numbers).** An earlier draft argued
for sequencing this *after* Canada and Australia impact upgrades, on the grounds that those
would retire three of the six bridges. **That was wrong on both counts** — see
[`../internal/impact_sources_scout.md`](../internal/impact_sources_scout.md):

- Canada is **not** being upgraded. StatCan publishes recovery spending with no per-business
  average, and "recovery spending" is narrower than loss (it excludes business interruption,
  lost revenue, ransom and legal). The decision was to leave Cyentia in place and label
  Canada known-weak rather than substitute a narrower measure that looks like an upgrade.
- Australia's ASD figure is `impact.min`; the Cyentia bridge in `au_finance_ransomware` is
  `impact.max`. It was never going to be touched.

No bridge is retired by that scout, so **there is no sequencing reason to delay**. If
anything the scout strengthens the case: Canada is now a deliberately-retained bridge, and
deliberate retention is only defensible if it is visible.

Parts 3 and 4 (declared shared bridges, documented transfer rules) matter most for
**Singapore**, whose entire impact side is borrowed US data and for which no local source
has been found.

When it lands, take the headline drop deliberately and publicly, with a `revisions/`
entry explaining it — the mechanism built for exactly this kind of change. A metric that
goes down for a stated reason is more credible than one that only ever goes up.

**Open questions for the owner:** whether the relationship is a field on the existing
record or a separate declared object; whether the migration is retroactive or new-records-
only; and what the coverage tools report as the headline once the two categories split.

## Implementation decisions (owner-approved 2026-08-01, implemented same day)

- **Field on the record**, two layers: `population_match` stores the fact about the record
  (specific declared applicability beyond the source's measured population); the per-shard
  card view combines it with a **country-strict** consumption check — a record whose
  applicability does not name the shard's own country (a global survey, or a foreign
  declaration reached by direct calibration reference) is bridged on country for that shard.
  Sector/size/threat come from the stored layer only: honest wildcard declarations are
  dilution, carried by the caveat, not counted as borrowing.
- **Same-survey adjacent-band anchors** (a floor from the small-business band or a stress
  from the large-business band of the shard's own country survey), documented single-case
  anchors and statutory parameters are the range-anchoring **method**, not borrowing: matched.
- **Retroactive**: all 120 source-backed records classified; the field is schema-required
  for `evidence_type: source_backed`.
- **Headline**: "N cell-matched · M bridged, of which K cross-country". Measured result on
  implementation: **28 cell-matched · 38 bridged (26 cross-country) of 66** — larger than
  this ADR's rough 6–7, which was measured on impact parameters only and before the
  country-strict rule was chosen. The drop is the point; the `revisions/` entry records it.
