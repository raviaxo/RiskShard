# Insider Misuse & Third-Party Outage — threat-specific impact pre-scout

*Researched 2026-07-24. **Not applied** — evidence write held for an approve-each-anchor pass
because the triangle shape and tail selection are consequential modeling calls, not mechanical.
Retires the tracked gap: both threats' impact sides currently rest entirely on generic
cross-cyber Cyentia bridges ($266k / $3M / $32M), not threat-specific data.*

## Insider Misuse — impact (source: Ponemon/DTEX *Cost of Insider Risks Global 2023*)

Fetched & citable (`curl/8.4.0` gets HTTP 200 from ponemonsullivanreport.com; ready to register):
- **Malicious insider: $701,500 per incident** (6.2 incidents/yr avg).
- **Credential theft: $679,621 per incident.**
- Negligent: 55% of incidents, $7.2M *annual* remediation (per-incident not cleanly stated).
- Total annualized insider-risk cost per org: $16.2M (aggregate of many incidents — **wrong basis**
  for a per-event impact anchor; do NOT use as impact.max).

**Proposed anchors + the open calls (need a decision):**
- `impact.likely` = **$701,500** (malicious insider — the deliberate-misuse type; clean, direct). ✅
- `impact.min` — **open.** Ponemon gives no per-incident figure below ~$680k, so a true floor isn't
  in this source. Options: (a) credential theft $679,621 (makes min≈likely — degenerate PERT body);
  (b) keep a lower generic floor, honestly labeled; (c) find a small-insider-incident source.
  *Recommend (b) short-term with a loud "floor is generic, not insider-specific" caveat, or defer
  until a genuine insider floor source is found.*
- `impact.max` — **open (tail selection).** Ponemon has no per-incident tail. A documented DOJ
  insider trade-secret case gives a real tail — candidates: **Kexue Huang $7–20M** (DOJ, sentenced;
  representative multi-$M) vs Motorola/Hytera $214M (mega-corp outlier, likely too large for
  mid-market). *Recommend Huang ~$20M as a documented, non-outlier tail — but this is a judgment
  call worth confirming.*

**Loud caveat to carry:** Ponemon per-incident is average *remediation* cost, tight around ~$700k;
it understates catastrophic insider fraud/IP-theft. Pairing a ~$700k body with a documented $20M
tail is honest but produces a spike-plus-fat-tail shape — state it.

## Third-Party Outage — impact + frequency (source: Uptime Institute *Annual Outage Analysis 2024*)

- **54% of significant outages exceed $100k; 20% exceed $1M** (threshold data, not a $ triangle).
- Third-party sites cause ~10% of major downtime (a *share*, not a per-org prevalence).
- **`frequency.max` is still a labeled interpretive estimate** (the tracked weakness). Uptime's 10%
  third-party-share is not a directly-reported per-org prevalence, so it does NOT cleanly retire the
  estimate. **Needs a directly-reported third-party-outage prevalence source** — still open.

**Assessment:** TPO needs (a) a $ triangle derived from Uptime's threshold bands (min $100k floor is
clean; likely/max need bands the exec summary may not give — check the full report), and (b) a real
frequency.max prevalence source. More sourcing required than Insider; treat as a separate objective.

## Recommendation

Do **Insider Misuse impact** first once the min-floor and tail calls are confirmed (likely is clean).
Do **TPO** as its own pass — it needs the full Uptime report for impact bands and a new prevalence
source for frequency. Both stay `governed_starter` with the weakness visible until then.
