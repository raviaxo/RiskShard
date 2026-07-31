# Pre-scout — DORA major-incident reporting (verified at source, 2026-07-28)

*Research note. Figures below were read from the primary PDF, not from secondary
coverage — two of them differ in meaning from how the trade press reported them.*

**Source:** ESAs (EBA / EIOPA / ESMA Joint Committee), **JC 2026 16, "2025 Report on
major ICT-related incidents", published 03 June 2026** — the first annual report under
Article 22(2) of DORA. Fetched from the EBA site (HTTP 200, 867 KB PDF).

## What it gives us — frequency, and it is strong

> "Overall, 3,383 major incidents (corresponding to an average of **0.18 major ICT
> related incidents per financial entity subject to DORA**) were reported in 2025 across
> all financial sectors in the EU" — Executive Summary, p.4

A **directly reported per-entity annual rate** from a supervisory authority, not a
denominator we constructed. That is rarer and stronger than most frequency evidence in
the repo.

Third-party origin, from Figure 8 (p.15) and §19 (p.14):

| | share |
|---|---|
| originated from an ICT third-party provider (TPP) | **29%** |
| not originated from a TPP | 68.9% |
| unknown / missing | 2.13% |

Root causes (§19): system failure/malfunction ~50%, external events 32%, process failures
19%, human error 12%.

**Candidate anchor for Third-Party Outage:** 0.18 × 0.29 ≈ **0.052 TPP-origin major
incidents per financial entity per year**.

### ❌ It does NOT retire TPO's `frequency.max` — assessed 2026-07-28, rejected

Checked against the actual records in `evidence/third_party_outage.yaml` before use. It
fails on **basis**, not on quality:

| | current TPO frequency set | DORA figure |
|---|---|---|
| `frequency.min` 0.44 | share of BCI respondents naming third-party failure their **top cause** of disruption | — |
| `frequency.likely` 0.80 | share of organisations experiencing **any** supply-chain disruption in the year | — |
| `frequency.max` 0.90 *(estimated)* | interpretive conversion from multi-event findings | — |
| | organisation-level **annual prevalence of experiencing a disruption**, broad and all-cause | **rate of supervisory-classified *major* incidents per entity**, EU financial entities only |

Three incompatibilities, any one of which is disqualifying:

1. **Different construct.** The existing set measures *did an organisation experience a
   disruption* (a prevalence, capped at 1.0). DORA measures *how many major incidents per
   entity* (a rate). They are not the same quantity.
2. **Different severity threshold.** DORA "major" is triggered by materiality thresholds
   in Delegated Regulation (EU) 2024/1772, and two thirds of those incidents caused no or
   minor disruption. BCI counts any disruption at all.
3. **It is ~17× *below* the existing minimum** (0.052 vs 0.44). A value that low cannot be
   a `max` under any reading; and slotting it in as a `min` would mix two bases inside one
   parameter triple, which is worse than the labeled estimate it would replace.

Using it would have looked like an upgrade — official supervisory source, directly
reported rate, retires an estimate — while quietly committing exactly the category error
this project exists to prevent. **`frequency.max` stays a labeled estimate.**

**What the figure legitimately supports instead:** a *separate, differently-defined*
scenario — "major ICT incident originating from a third-party provider, EU financial
entity" — where 0.052 is the correct and well-defined frequency. That scenario is
buildable the moment an impact side exists for it, which today it does not (see below).
Parked, not discarded.

**Correction to the secondary coverage.** Press reporting conflated two different
figures. The Executive Summary says "almost one third of major incidents originated from
failures attributable to **third-parties (including ICT third-party providers, other
financial entities, and infrastructure providers)**" — a *broader* category — while
Figure 8's 29% is specifically **ICT third-party service providers**. Use the 29% and cite
Figure 8; do not describe it as "all third parties".

## What it does not give us — impact, decisively

§3.5 "Costs incurred" (p.17). Financial entities **are** required to report gross direct
and indirect costs and losses, including foregone revenues, software replacement, staff
overtime, customer compensation and contractual non-compliance. The result:

> "Based on the available information, it seems that major incidents had a very limited
> monetary impact: half of them did not report any direct or indirect costs (almost 40%)
> or indicated to have suffered a negligible monetary impact, with direct and indirect
> costs amounting to less than EUR 1,000 (around 10%). An additional 15% did not fill the
> relevant field."

The report's own footnote 23 notes this "may point to incorrect reporting practices".
Recoveries are worse: ~⅔ reported none, another ⅓ used reporting logic that "could not be
reconciled for analytical use", and only ~3% reported a positive amount.

**Conclusion: DORA cannot supply impact evidence in this edition.** The cost fields are
mostly empty, zero, or unreliable, and the ESAs say so themselves. A new IT tool with
automated validation arrives in 2026, so the **2026 edition (due ~June 2027) is worth
re-scouting** — but nothing usable for impact exists today.

## The caveat that must travel with any use of 0.18

> "two thirds of major incidents resulted in no or minor disruption to clients and
> transactions" (Exec. Summary, p.4); impact on clients absent or minor in almost 60% of
> cases (§22); two thirds affected no transactions or fewer than 1,000 (§23)

A **"major incident" under DORA is a supervisory classification, not a loss event.** It is
triggered by materiality thresholds in Delegated Regulation (EU) 2024/1772, and most such
incidents cost the entity little or nothing. Using 0.18 as a *loss-event* frequency would
overstate badly — this is the same attack-prevalence-vs-loss-event trap already caveated
on the JP shard, and it must be equally loud here.

Other limits to record: only incidents with a final report by the 5 Feb 2026 cutoff;
"divergent reporting practices across sectors and jurisdictions are still observed";
first year of a new regime, so the series has no history yet; EEA coverage is partial
(Norway from 1 July 2025, Iceland only from 2026).

## Bonus — two documented availability events, both EU, one Spanish

Useful as scenario anchors (durations are documented; **no euro losses are given**):

- **TARGET2 (27 February 2025)** — T2 and T2S unavailable for approximately **10 and 8
  hours** respectively, ~1 hour partial disruption to TIPS; securities settlement,
  payments and liquidity transfers suspended for several hours. Root cause: a rare
  hardware malfunction in a core storage component (§33–35).
- **Iberian Peninsula blackout (28 April 2025, 12:30 CEST)** — total failure of the
  Spanish electrical grid, also hitting Portugal, for approximately **10 hours**. Bank and
  insurer data centres stayed up on backup generators, but branches lost power and
  connectivity, POS terminals failed, and mobile/web banking access was impaired (§36–37).

The Iberian blackout is a genuinely Spanish, genuinely availability-shaped, officially
documented event. Note it is a **power-grid** failure, not a cyber attack — honest use
would be as an external-event availability scenario, never as evidence of cyber frequency.

## Registered 2026-07-30

The report is now a gathered source (`esas_dora_major_ict_incidents_2025`, 867 KB PDF,
sha256 `aecab177…`) and both verified anchors are evidence records in
`evidence/third_party_outage.yaml`:

- `esas_dora_2025_major_ict_incident_rate_per_entity` — 0.18, unit `annual_rate_per_entity`
- `esas_dora_2025_third_party_origin_share` — 0.29, unit `proportion`

**Deliberately not selected by any calibration.** They are on a different construct from the
BCI/Interos organisation-level prevalence records in the same file, and mixing the two inside
one parameter triple would be the category error this note already documents. The units say so
explicitly — an annual *rate per entity* can exceed 1 and is not an annual probability.

They are held as candidates for a separate DORA-basis scenario, which remains blocked on impact.

## Net position

- **Frequency for the EU financial sector: solved**, and it complements Eurostat exactly
  (Eurostat excludes finance; DORA is finance-only). See
  [`coverage_harvest.md`](coverage_harvest.md).
- **Impact: still unsolved, now for a second independent reason.** Spanish public bodies
  publish counts rather than euros; DORA mandates euros but the field is unreliable.
  Remaining candidates: Uptime Institute outage-cost bands, cyber-insurance claims
  studies, and the 2026 DORA edition.
