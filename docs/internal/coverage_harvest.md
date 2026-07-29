# Coverage harvest — what the sources already scouted could support (2026-07-28)

*Research note. Prompted by an observation worth taking seriously: we keep scouting
sources one shard at a time, while the reports being read cover far more ground than the
single shard in front of us. This quantifies what is actually reachable.*

## Current state

**11 shards · 8 countries · 3 threat families** (BEC, data breach, ransomware). Every
shard was built by hunting sources for that specific cell.

## Finding 1 — Eurostat already covers the frequency half of 35 countries

`isoc_cisce_ic`, size class **50–249** (the `mid_market` cell), reference year 2024,
percentage of enterprises, fetched from the dissemination API:

| geo | avail. via attack | disclosure via intrusion | destruction via malware | any incident |
|---|---|---|---|---|
| ES Spain | 5.07 | 2.24 | 3.31 | 23.11 |
| DE Germany | 4.24 | 1.86 | 1.80 | 30.39 |
| FR France | 3.65 | 2.00 | 4.24 | 34.58 |
| IT Italy | 4.27 | 1.86 | 1.86 | 19.81 |
| NL Netherlands | 6.59 | 4.21 | 1.88 | 33.92 |
| FI Finland | 7.05 | 3.55 | 1.77 | 46.76 |
| PL Poland | 3.96 | 1.25 | 3.08 | 40.57 |
| IE Ireland | 1.19 | 2.35 | 1.48 | 16.65 |
| **EU27** | **4.34** | **2.22** | **2.34** | **27.97** |

…and 26 more, including all EU member states plus NO, TR, RS, BA, ME, AL. **35 countries
carry the mid-market availability indicator for 2024**, with a 2022 series alongside it
(2019 is present in the dimension; values not verified for every cell).

Three of the indicators map onto threat families directly:

- `E_SEC2IUSVA` → **availability / service disruption by outside attack** (a threat the
  repo does not model at all today)
- `E_SEC2ICNFA` → **data breach** (disclosure via intrusion, pharming, phishing)
- `E_SEC2IDCDA` → **destructive malware / ransomware-adjacent** (data destruction or
  corruption via malicious software or intrusion)

So the *frequency* side of roughly **35 countries × 3 threats** is reachable from one
official statistical source, with a real multi-year band rather than a single survey
point — and it is stronger evidence than several anchors currently in the repo, which
rest on vendor attack-prevalence surveys.

**Known limits, unchanged:** the survey excludes the financial sector entirely, and size
specificity and sector specificity are mutually exclusive across the two tables (see
[`es_availability_prescout.md`](es_availability_prescout.md)).

## Finding 2 — DORA fills exactly the sector Eurostat excludes

**ESAs 2025 Report on major ICT-related incidents** (EBA/ESMA/EIOPA, published
2026-06-03, covering 2025 — a fetchable PDF on the EBA site):

- **3,383 major incidents** reported across the EU financial sector
- ≈ **0.18 major ICT-related incidents per financial entity subject to DORA** — a
  *directly reported per-entity annual rate*, not a denominator we had to construct
- **29%** originated from **ICT third-party service providers**
- 51% system failures · 27% external events · 18% payment-related · 10% cybersecurity-related
- credit institutions >60% of incidents, payment services 16%; ~⅓ had cross-border impact

Two consequences:

1. It is a **financial-sector** frequency source, which is precisely what Eurostat cannot
   give — the two are complementary rather than overlapping.
2. **0.18 × 0.29 ≈ 0.052 major third-party-origin incidents per entity per year** is a
   candidate *reported* frequency for **Third-Party Outage**, whose `frequency.max` is
   currently a labeled interpretive estimate and is the last such estimate in the tracked
   queue. This may be the source that retires it.

**✅ Verified against the primary PDF 2026-07-28** — see [`dora_prescout.md`](dora_prescout.md).
The frequency figures hold. Two corrections came out of reading the source:

- The press conflated "29% from **ICT third-party providers**" (Figure 8) with a broader
  "third parties including other financial entities and infrastructure providers" in the
  Executive Summary. Use the 29% and cite Figure 8.
- **DORA does not supply impact**, despite Article 22(2) mandating cost reporting: half of
  major incidents reported no direct or indirect cost or under EUR 1,000, and a further
  15% left the field blank — which the ESAs themselves flag as likely mis-reporting. The
  hope that DORA would solve the impact half is dead for this edition; re-scout the 2026
  edition (due ~June 2027), which will have automated validation.
- A **"major incident" is a supervisory classification, not a loss event** — two thirds
  caused no or minor disruption. Using 0.18 as a loss-event frequency would overstate
  badly.

## The reframing

Frequency is no longer the bottleneck. **Impact is** — and it is the bottleneck for
*every* candidate shard simultaneously, not one at a time. The scouting pattern to date
(hunt both halves per cell) has been optimising the wrong half.

That suggests a different shape of work:

1. **Solve impact once per threat family**, properly and with honest caveats, rather than
   per country. Loss magnitude generalises across borders far better than frequency does
   — which is also what `IMPACT_UNCERTAINTY_NOTE` already says in the engine.
2. **Then** a single "Eurostat frequency pass" could raise many shards' frequency sides
   at once, each country-specific and size-specific.

## Risks this would create — surface before deciding

Mass expansion from one source is not free, and the project's own rules push back on it:

- **Correlated single-source dependence.** Dozens of shards resting on one Eurostat
  survey means one methodology change or discontinuity moves everything at once. Today's
  diversity of sources is itself a form of robustness.
- **Coverage inflating faster than trustworthiness.** "35 countries" reads as maturity;
  it would in fact be 35 countries sharing one frequency source and a common, bridged
  impact side. The maturity ladder and the strength ledger must not let shard *count*
  masquerade as evidence *strength*.
- **Caveat dilution.** Every shard would inherit the same limitations (finance excluded,
  incidents-with-consequences ≠ loss events, size/sector tradeoff). Repeated boilerplate
  caveats get skimmed; the project's "louder, not quieter" rule needs a deliberate answer
  for this.
- **Review capacity.** Nothing is benchmark-grade without human review. Multiplying
  shards multiplies the review debt.

**This is a strategy decision with no owner doc, so it is surfaced here rather than
acted on** (per `docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control). The options are
roughly: stay depth-first (few shards, strongest possible evidence), go breadth-first
(many shards, uniform bridged impact, loud shared caveats), or a middle path — expand
frequency coverage only where an impact source genuinely exists for that cell.

## Next verification steps

1. Pull the **ESAs 2025 DORA report PDF** and verify the 0.18/entity rate, the 29%
   third-party share, and the definition of "major incident" at source.
2. Confirm the Eurostat 2019 series values, and pin exact citation strings (dataset,
   extraction date, indicator definitions) for the manifest.
3. Impact hunt, per threat family — Uptime Institute outage bands, DORA incident cost
   data if any exists, cyber-insurance claims studies.
