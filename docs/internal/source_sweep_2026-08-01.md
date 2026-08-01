# Source sweep — 2026-08-01

The deliberate version of the accidental IBM edition-roll catch (2026-07-31): every
registered source re-gathered into temp paths, sha256 diffed against the committed
manifest, and every changed artifact grepped for the exact figures its evidence
records cite. Method: `gather_sources.py` into scratch, then per-record token
matching of `citation_detail` figures against artifact text (pdftotext for PDFs,
tag-stripped HTML otherwise), with manual inspection of every miss.

## Headline result

**52 registered sources. No cited figure has drifted.** Every miss the sweep found
was present from birth: the gathered artifact never carried the figure, or the URL
never pointed at the document it claimed to. Values themselves all check out where
verifiable; this was a provenance-strength audit, not a correctness incident.

- **13 byte-identical** (all PDFs, the Eurostat JSON, 3 stable HTML pages).
- **37 changed HTML** — for 31, every cited figure still present (chrome churn only).
  One false alarm in the tooling: `ibm_france` renders "4,65 millions d'€" in French
  locale; the matcher wanted "4.65".
- **2 registered but never gathered** — both are `active: false` inactive candidates
  (`first_epss_data_stats`, `asd_annual_cyber_threat_report_2024_2025`), documented
  in the registry. This closes the "unresolved" note from 2026-07-30: they are not
  gaps, they are parked deliberately.

## url_stability: 47 unknowns classified

Now **44 dated / 8 rolling** across all 52 (was 5 dated / 47 unknown). `rolling`
means the URL will drift from the citation by design; doctor lists these for
re-verification on every run: `privacy_act_1988_latest` (a /latest alias),
`apra_cps_230` (redirects to the current standard), `gdpr_article_83` (living CNIL
FAQ), `business_qld`, `ico_self_reported_breach_cases_2024_25`, `interos`,
`first_epss_data_stats` (live stats page), and `deepfake_business_impact_2024`
(guide rewritten in place). *(Corrected 2026-08-01, same day: an earlier draft of
this note listed 42/10 and wrongly included `bci` and `gurucul_insider_risk_report_2026`
in the rolling set.)*

## Six artifacts never evidenced their cited line — 4 fixed, 2 documented

| Source | Problem found | Action taken |
|---|---|---|
| `cybersecurity_insiders_insider_threat_2024` | Registered URL (missing the `-gurucul` suffix) 301s to the site homepage; the artifact was unrelated content | Re-pointed to an immutable archive.org snapshot of the real report page. **Gap remains:** the 66%/76% stats are inside the gated PDF, not on the page — record review queued |
| `afp_payments_fraud_2025` | Live AFP page no longer states the 63% BEC prevalence | Re-pointed to an archive.org snapshot verified to carry "63% of respondents" ✓ |
| `census_susb_2022` | Registered page is a tables index with no totals | Re-pointed to the actual SUSB US/state/NAICS/LFO xlsx; US all-sector row = **6,198,713 employer firms**, verified in artifact ✓ |
| `ico_monetary_penalties_2024` | Live URM page edited; GBP 17.5M statutory max and fine-count context absent | Re-pointed to an archive.org snapshot carrying GBP 12.7M and 17.5M ✓. Registry now notes the 12,412 denominator belongs to `ico_self_reported_breach_cases_2024_25` |
| `bci_supply_chain_resilience_2024` | 43.6% third-party-failure figure is only in the gated report PDF — never on the landing page, current or archived | KNOWN GAP note in registry; record review queued |
| `deepfake_business_impact_2024` | USD 500k/603k absent from the page even in the snapshot taken on the extraction date; figures resemble Regula survey numbers (Regula artifact says ~USD 450k avg) — likely misattributed | KNOWN GAP note in registry; record review queued |

Also: `abs_characteristics_australian_business_2025` was registered on the ABS
`/latest-release` alias — the exact ibm.com failure mode, one ABS release away from
silently swapping editions. Re-pointed to the edition-pinned `/2024-25` URL
(verified: "21%", "one in five" present).

## Follow-up — queued as an evidence objective (approve-each-anchor)

**Record-level review of 3 evidence records** whose figures cannot currently be
verified against any gathered artifact:

1. `insider_misuse.yaml` — 66%/76% prevalence (frequency.min/likely). The Gurucul
   landing page's own "76%" is a *different* statistic (complexity-as-driver). The
   true attack-prevalence stat needs the report PDF or a citable secondary.
2. `third_party_outage.yaml` — 43.6% (frequency.min). Needs a public artifact
   carrying the figure, or the record re-anchored to what the landing page does
   state (~80% disruption prevalence is verifiable).
3. `ai_enabled_fraud.yaml` — USD 500k/603k (impact.likely). Likely belongs to the
   Regula survey, whose artifact reports ~USD 450k average. Reattributing changes
   the record's source and possibly its value.

Plus one nuance, no action needed until that review: the SUSB artifact states
6,198,713 firms; the record frames the denominator as "~6.1M" (range 5.52M–6.3M
across programs). The derived 0.004 floor is unchanged either way (24,768 /
6,198,713 = 0.0040).

## What the sweep did *not* find

No edition rolls, no silently changed figures, no dead URLs among active sources.
The 2026-07-31 `url_stability` hypothesis held: the risk concentrates in
`/latest`-style aliases and living pages, and those are now labeled and
doctor-reported.
