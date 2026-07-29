# Pre-scout — Spain shard + availability threat (2026-07-28)

*Research note, not a build. Candidate anchors and the gaps that would need an
approve-each-anchor decision before any of this becomes evidence. Nothing here is
committed to the model yet.*

## Why these two together

Spain adds a 9th country and the first Spanish sources in the manifest (currently
**0 of 48**). Availability adds the first threat outside the BEC / data-breach /
ransomware trio — the CIA gap. They turn out to share one source, which is why they
were scouted together.

## The find: Eurostat `isoc_cisce_ic` — official, country- and size-specific

EU statistical office, **Spain-specific, split by enterprise size class including
`50-249` (exactly the repo's `mid_market` cell)**, reference years 2019 / 2022 / 2024,
fetched live from the Eurostat dissemination API (HTTP 200, machine-readable JSON).

Spain, size 50–249, **percentage of enterprises**:

| Indicator | 2022 | 2024 |
|---|---|---|
| `E_SEC2IUSVA` — unavailability of ICT services **due to outside attack** (ransomware, DoS) | 5.60 | **5.07** |
| `E_SEC2ICNFA` — disclosure of confidential data due to intrusion / phishing | 2.42 | **2.24** |
| `E_SEC2IDCDA` — destruction / corruption of data due to malware or intrusion | 3.79 | **3.31** |
| `E_SEC2IANY` — any ICT security incident | 25.29 | **23.11** |

This is stronger than most frequency evidence currently in the repo: an official
statistical office rather than a vendor survey, the exact country, the exact size band,
a real multi-year series (so min/likely/max is an *observed* band, not an invented one),
and it measures **incidents with consequences**, which is much closer to a loss event
than the attack-prevalence anchors the JP and AU shards rest on.

`E_SEC2IUSVA` is the availability threat, already quantified per country and size —
and the same dataset covers **DE and FR**, which are existing shards.

## Two blocking constraints — both must be caveated, not hidden

**1. The financial sector is excluded.** The NACE coverage is literally
`C10-S951_X_K` — "All activities … **without financial sector**". Confirmed against the
sector dimension: there is no `K` anywhere in the dataset. So this evidence **cannot**
support an `es_finance_*` shard, which is what the repo's existing pattern would suggest.
A Spain shard on this data must be a sector Eurostat actually covers.

**2. Size specificity and sector specificity are mutually exclusive.** The size-split
dataset (`isoc_cisce_ic`) is all-sector; the sector-split dataset (`isoc_cisce_icn2`) is
all-sizes (10+). You can have one or the other:

| Spain, 2024, 10+ employees | any incident | disclosure via intrusion | unavailability via attack |
|---|---|---|---|
| C — Manufacturing | 15.94 | 1.24 | 2.09 |
| H — Transportation and storage | 12.94 | 1.39 | 2.55 |
| J — Information and communication | 26.60 | 2.06 | **9.22** |
| M — Professional, scientific, technical | 23.21 | 2.43 | 4.29 |
| G — Wholesale and retail trade | 14.87 | 0.83 | 3.06 |

Mixing the two bases in one shard (sector for `likely`, size band for `min`/`max`) would
need a loud caveat that the denominators differ.

## Impact — the real gap

Eurostat gives frequency only. There is **no Spanish loss-magnitude data** in it, and
Spain has no equivalent of IBM/NetDiligence country breakouts. What exists:

- **AEPD Memoria 2025** (published ~May 2026): total sanctions **€48,108,765** across
  **326** sanctioning procedures → **average fine ≈ €148,000** (+17% YoY). Data-breach-
  linked procedures rose 157% (30 → 77), carrying nearly **€20M** → ≈ **€260k** average
  for the breach-specific subset.
- **INCIBE Balance 2025** (published Feb 2026): 122,223 incidents managed (+26%);
  ransomware **392**; 60% of incidents hit SMEs and self-employed. Sector split: banking
  34%, transport 14%, energy 8%.

Both are **counts and penalties, not loss magnitudes**. AEPD fines are a *regulatory
penalty*, not total event loss — using them as `impact.likely` would be the exact
category error the project exists to prevent.

**The honest shape** is the pattern already proven by
`gb_finance_data_breach_regulatory_chain`: an EU/global-bridged loss body (loudly
caveated as not Spain-specific) plus a **Spain-specific AEPD regulatory-penalty
loss-stage** (ADR-0001), where the penalty drives the tail rather than the mean. That
makes the Spanish evidence carry the part it can genuinely support.

INCIBE's 122,223 is a **reported/managed floor**, not prevalence — the same shape as the
IC3÷Census anchor already in the US shard, and it must carry the same caveat.

## Candidate build (needs approve-each-anchor)

An availability shard is the stronger of the two, because Eurostat supports **five of
six parameters' worth of frequency reasoning directly**:

- `frequency.min` 0.0507 — Spain, 50–249, 2024, `E_SEC2IUSVA`
- `frequency.likely` / `max` — the 2022 value (0.056) and/or a sector figure, e.g. ICT at
  0.0922, with the denominator-mismatch caveat
- impact — **unresolved.** ICT-outage loss magnitude for Spanish mid-market is not in any
  source found today. Options to scout next: Uptime Institute outage severity bands
  (paywalled?), ENISA, or a documented Spanish incident. **Do not build until this is
  answered** — an availability shard with a bridged impact side would repeat the
  Insider/TPO generic-bridge weakness the queue is already trying to retire.

## Round 2 — Spanish national, regional and EU sources (2026-07-28)

Scouted INCIBE, CCN, the autonomous-community agencies and EU bodies specifically for
**impact**. Headline finding: **Spanish public bodies publish counts and typologies,
almost never euros.**

**National**
- **INCIBE Balance 2025** (Feb 2026) — 122,223 incidents managed (+26%); malware 55,411;
  phishing/online fraud 25,133; **ransomware 392**; 60% hit SMEs and self-employed;
  sector shares banking 34%, transport 14%, energy 8%. *Counts only.* Reported/managed
  floor, same shape as the IC3÷Census anchor — usable for a frequency floor, **not** for
  impact.
- **AEPD Memoria 2025** — €48,108,765 total sanctions over 326 procedures (avg ≈
  **€148,000**); breach-linked procedures 30 → 77 (+157%) carrying ≈ €20M (≈ **€260k**
  average). *Regulatory penalty only* → loss-stage material, not `impact.likely`.

**Regional** (checked because coverage is genuinely devolved in Spain)
- **Agència de Ciberseguretat de Catalunya**, Memòria 2025 — 6,544 incidents handled
  (+94% vs 3,372 in 2024); credential leaks 3,427, unauthorised access 2,573, malware
  367; 26 crisis-committee activations; >9.1bn attack attempts detected. **But the
  population is overwhelmingly public sector** (university 2,931, health 2,162,
  Generalitat departments 1,962) — *not* mid-market enterprise, so it does not fit the
  shard cell. No euro figures.
- **Basque Cybersecurity Centre (BCSC)** — quarterly incident counts (e.g. 235 in one
  2022 quarter: fraud 142, abusive content 34, intrusion 25) and a survey datapoint that
  **64% of attacked Basque firms paid a ransom, and almost half were attacked again**.
  Interesting behavioural evidence; no loss magnitudes found.

**EU-level — the only credible euro anchors found**
- **ENISA NIS Investments** — verified at source: *"The banking and healthcare sectors
  are the sectors suffering the highest direct costs of major security incidents when
  they happen, usually ranging from 213 000 to 300 000 EUR when the usual direct cost is
  about 100 000 EUR."* Population: **947 Operators of Essential Services and Digital
  Service Providers across all 27 Member States** (2021 edition; later editions report a
  higher median, to be pinned before use). **Critical caveat: OES/DSP are large,
  in-scope-of-NIS entities — applying this to mid-market almost certainly overstates.**

**Rejected — do not register**
- The Spanish SME cost figures circulating in trade press are mutually inconsistent and
  mostly untraceable to a method: €2,500–60,000, €35,000–80,000, €75,000, €15,000–50,000
  all appear as "the average cost of an attack on an SME" in 2025-26 articles. Without a
  published methodology these fail the source bar.
- The widely repeated **"60% of SMEs close within six months of a serious incident"** is
  a well-known zombie statistic with no traceable primary source. It must not enter the
  evidence base, and is noted here so a future contributor does not re-import it.

**Net position on impact:** still unresolved for Spanish mid-market. The best available
is an EU-level ENISA figure derived from large essential-service operators, which would
be a *bridge with a loud size-mismatch caveat* — the same category of weakness the
Insider/TPO objectives are trying to retire. Worth scouting next: Uptime Institute
outage-cost bands, DORA major-incident reporting (EU financial entities, from 2025),
and Spanish cyber-insurance claims data (UNESPA or broker loss studies).

## Recommendation

1. Verify the 2019 datapoint and pull the exact Eurostat citation strings (dataset,
   extraction date, indicator definitions) for the manifest.
2. Resolve the **impact** side before committing to a shard. Frequency is the strong
   half; impact is where this either becomes honest or becomes another bridge.
3. Sector choice, if a Spain shard proceeds: manufacturing (`C`) makes it directly
   comparable to the existing DE and JP manufacturing shards. **Not finance.**

## Sources to register if this proceeds

- Eurostat `isoc_cisce_ic` / `isoc_cisce_icn2` — official statistics, API-fetchable
- AEPD Memoria Anual 2025 — regulatory penalty stage only
- INCIBE Balance de Ciberseguridad 2025 — reported-incident floor, sector shares
