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
