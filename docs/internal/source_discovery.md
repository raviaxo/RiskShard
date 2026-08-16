# Source discovery — where cyber-loss data actually lives, and which channels work

*Tested 2026-08-16. Every claim below was tried, not assumed; the failures are as useful
as the successes and are recorded with the same weight.*

## The problem

The corpus reached 69 registered sources by accretion — things that came to hand, mostly
English, mostly vendor studies. [The research plan](research_plan.md) can order what
arrived. It cannot tell us what we never looked for, and that gap was the honest weak point
of the whole programme.

This page is the first systematic pass at it: **which discovery channels produce usable
sources, and which produce noise.**

## Channels tested

| channel | result | evidence |
| --- | --- | --- |
| **Vendor landing page → linked PDF** | ✅ **works, and we were losing sources to it** | All three Cyentia IRIS studies and the Interos report were one ungated link from pages already in the corpus. The registry pointed at the page; the gather stored the page. |
| **Direct asset hosts** | ✅ works | `assets.sophos.com/...pdf` returns 200 to a plain request. |
| **GitHub, known-entity enumeration** | ✅ works | `sophoslabs/Active_Adversary_Report` (14★) and `vz-risk/VCDB` (668★) both resolve and both ship data. |
| **GitHub, keyword search** | ❌ **noise** | *"cyber incident loss dataset"*, *"ransomware payments dataset"* → student coursework, SQL exercises, empty repos. Best hits were 0–2★ analyses that merely *point* at a primary source. |
| **Bot-protected vendor sites** | ❌ blocked | `sophos.com/en-us/blog/...` and `ibm.com/reports/data-breach` return empty to automated retrieval. These genuinely need a person. |
| **Regulator open data** | ✅ **richest per unit of effort** | The ICO publishes quarterly personal-data-breach CSVs — 3,497 case-level rows in one quarter, with sector, sub-sector, named organisation and a cyber-incident flag. |

**The most valuable lesson is the first row.** The biggest single gain today came not from
finding new sources but from noticing that sources we already had were stored as landing
pages. **Before hunting, re-check what the corpus thinks it holds.**

## The structural finding

Having profiled the open datasets against the gated reports, the split is not random:

> **Open, redistributable cyber data is overwhelmingly *technical*. The *money* is in gated
> vendor surveys and paywalled commercial databases.**

- **VCDB** — 10,042 incidents, open, VERIS-schema, country + NAICS + employee band. **324
  carry a loss amount**, and those run 2012–2016 with three records in 2021.
- **Sophos Active Adversary Report** — 661 incidents, open CSV on GitHub, country × org size
  × attack type, dwell time, root cause, exfiltration volume in GB. **396 of 661 fall in the
  100–5,000 employee band.** It carries **no monetary column at all**: `impact` is
  categorical (*"Data Encrypted for Impact"*).
- **Sophos State of Ransomware** — the money (median demand, median payment, share ≥ $1M) is
  in the *gated survey PDFs*, from the same vendor.

The same company publishes incident mechanics openly and loss magnitudes behind a form. That
is the shape of the whole field, and it explains why a project trying to govern *loss*
evidence keeps hitting gates while a project studying *attack technique* does not.

**Consequence for us:** open datasets are strong for frequency, conditional rates and
incident characteristics, and near-useless for impact. Expansion should not expect to find
an open loss corpus, because on this evidence there isn't one.

## Where to expand next, ranked

Ordered by expected yield against [our measured gaps](research_plan.md), not by ease.

1. **National CERT / CSIRT annual reports.** We hold ASD (Australia) and nothing else. Every
   country we model has one — BSI (DE), ANSSI (FR), NCSC (GB), NISC/JPCERT (JP), CSA (SG),
   CCCS (CA), CISA (US). They are public, ungated, and published on a predictable annual
   cadence. **Highest-yield unexplored class.**
2. **Insurance regulators and broker aggregates.** The AMRAE *LUCY* study (France) surfaced
   via a GitHub analysis repo that cited it — claims-based, which is the population most
   likely to carry both a magnitude and a denominator. NetDiligence is our only source of
   this type today.
3. **Statistical offices beyond the four we hold.** We use ABS, Census SUSB, Eurostat and
   SingStat as denominators. Destatis, INSEE, StatCan and e-Stat are the equivalents for
   cells we already model.
4. **Academic loss studies.** Entirely unexplored. Unlikely to be current, likely to be
   methodologically explicit — which is exactly what the audit's four questions reward.
5. **Further open incident datasets.** Low expected value for impact, per the structural
   finding, but cheap to check and useful for frequency.

## Method, so this is repeatable

1. **Re-check the corpus first** — is a source stored as a landing page rather than the
   document? That was worth more today than any new discovery.
2. **Enumerate known publishers**, do not keyword-search. Keyword search on GitHub returned
   nothing usable; naming `vz-risk` and `sophoslabs` returned two real datasets.
3. **Triage before reading** — [`sources/intake.yaml`](../../sources/intake.yaml) scores a
   candidate's promise against measured gaps, so a document that cannot serve a cell we model
   is parked rather than read.
4. **Read, then admit** — registry entry, manifest hash, then an audit row. A source is not
   admitted because it is interesting; it is admitted because it answers something.

## What this page does not claim

This is one afternoon of channel testing against a corpus of 69. It does not establish that
national CERT reports carry usable loss figures — only that they are the largest class we
have never looked at. **Every item in the ranking above is a hypothesis about yield, and the
audit is what would settle it.**
