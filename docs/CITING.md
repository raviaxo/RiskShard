# Citing a RiskShard number

Every parameter on the [explorer](https://raviaxo.github.io/RiskShard/) has a
**citable identifier** that pins it to an immutable, fingerprinted data release
([ADR-0004](adr/0004-citable-parameter-identifiers.md)):

```
RS:<shard_id>/<parameter>                    canonical (tracks latest)
RS:<shard_id>/<parameter>@<release>          pinned (immutable — use this in documents)
```

A pinned citation keeps resolving to the value it was written against, at
`https://raviaxo.github.io/RiskShard/r/<release>/`, even after the live figure
moves. The `[cite]` affordance on any parameter row copies the full citation —
value, source, publication date, **and the caveat** — to the clipboard. The
caveat travels inside the citation on purpose: a number quoted away from its
limits is how survey-summary telephone starts.

## Worked examples

**A risk-register row** (frequency input, UK data breach):

> Likelihood basis: 65% of UK medium businesses identified a cyber security
> breach or attack in the last 12 months (UK Cyber Security Breaches Survey
> 2025/26, official statistics).
> `RS:gb_finance_data_breach_midmarket/frequency.likely@2026.08.03-v0.4.0`
> Caveat carried: covers identified breaches *or attacks*, which overstates
> loss-event frequency.

**A board-deck footnote** (loss magnitude, AU financial services):

> ¹ Typical breach cost basis AUD 6.31M — IBM Cost of a Data Breach 2026,
> Australian financial-services average.
> `RS:au_finance_data_breach_midmarket/impact.likely@2026.08.03-v0.4.0`
> (enterprise-leaning study population; per-cell sample size unpublished).

**A prose sentence:**

> Australian mid-market organisations faced a 54% ransomware attack rate in the
> 2024 survey year
> (`RS:au_finance_ransomware_midmarket/frequency.likely@2026.08.03-v0.4.0` —
> attack prevalence, not loss-event frequency; all-sector sample).

## Rules that keep a citation honest

1. **Pin the release** in anything that outlives a browser tab. The canonical
   (unpinned) form is for conversation, not documents.
2. **Carry the caveat.** If there is no room for the full caveat, carry its
   sharpest clause. A RiskShard citation with the caveat stripped is a
   misquote.
3. **A renamed shard keeps resolving** through `aliases.yaml` — do not rewrite
   old citations after a rename.
4. If a cited figure is later revised or retracted, the pinned release still
   shows what you cited, and the live page's correction record (Note 2) shows
   what changed and why. Cite the correction too if you update the document.

To verify any citation against the governed evidence:

```bash
python scripts/riskshard_modules.py provenance <shard_id> <parameter>
```
