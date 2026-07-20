# NEXT_STEPS — active session queue

> Point Claude Code at this file to resume: **"Run /session:start, then resume Objective N from docs/NEXT_STEPS.md."**
> Drive mode for this queue: **approve each anchor** — Claude stops at every evidence
> decision (source trust, chosen value, caveat) and waits for a short yes / no / adjust.
> Designed to be driven from a phone: Claude fetches, extracts, drafts, and runs; the
> human only makes short approve/reject calls. No hand-editing of YAML required.

Work objectives **one at a time** to their Definition of Done. Order within the active
queue is **not fixed** — all four will be done; pick any to start. Do not pull the next
objective into scope until the current one is done.

**Shared Definition of Done** (every evidence objective below):
- `riskshard_modules.py coverage` (or `toprisks`) shows the target as **source-backed** / direct 6/6.
- `validate_evidence.py`, `contributor_preflight.py`, and the full test suite pass.
- New sources gathered into `sources/manifest.json`; calibration profile (if any) rewired
  to the source-backed evidence; a real calibrate + simulate run succeeds with 0 warnings.
- Caveats kept **louder, not quieter** (denominator range, attempts-vs-loss-events, sample skew).
- **Re-run the full suite after the calibration rewire** — the rewire shifts benchmark
  blocker counts (learned 2026-07-20: `test_benchmark_program` asserts a snapshot count).
- Committed `-s` (DCO) on a scoped branch; not pushed unless asked.

---

## Active queue — P2 cycle (any order)

### Objective 4 — Insider Misuse: add source-backed frequency evidence  ✅ DONE 2026-07-20
**Result:** Insider Misuse now **6/6 direct** (was 3/6). New `evidence/insider_misuse.yaml`:
`frequency.min` 0.66 (Cybersecurity Insiders 2019 baseline), `frequency.likely` 0.76
(Cybersecurity Insiders 2024), `frequency.max` 0.90 (Gurucul 2026 Insider Risk Report).
Broad insider-exposure bridges (incl. negligent insiders), caveated as overstating deliberate
misuse. No calibration to rewire; full suite clean. **Follow-up surfaced:** readiness now asks
for an *Insider Misuse calibration profile* (to make it a runnable shard) — a future objective.
Top-risk `Insider Misuse` is 3/6 direct (impact side covered; **frequency.min/likely/max
missing**, 0 assumptions). Add source-backed frequency.
- **Candidate sources:** Verizon DBIR 2026 (already in-repo) privilege-misuse / insider
  share of breaches; Ponemon or DTEX *Cost of Insider Threats* (incidents per organization
  per year → per-org annual frequency); Cyentia for tail.
- **3 approve-points:** frequency.min / likely / max.
- Scenario `scenarios/insider_threat.yaml` exists; no calibrated module yet — confirm the
  wiring (module/calibration) or note it as scaffold-only.

### Objective 5 — Third-Party Outage: add source-backed frequency evidence
Top-risk `Third-Party Outage` is 3/6 direct (**frequency.min/likely/max missing**, 0 assumptions).
- **Candidate sources:** DBIR third-party-involvement share (already in-repo as context, 0.48);
  Uptime Institute *Annual Outage Analysis* (outage frequency/severity); a supply-chain /
  third-party incident-rate source for per-org annualization (the fuzzier part — flag the
  denominator assumption loudly).
- **3 approve-points:** frequency.min / likely / max.

### Objective 6 — `sg_finance_bec_midmarket` → source-backed (1/6 → 6/6)
5 assumptions to replace; `impact.likely` already source-backed (IC3 global-BEC-as-SG-context).
Reuse the US BEC pattern built 2026-07-20.
- **5 approve-points:** frequency.min/likely/max, impact.min, impact.max.
- **Candidate sources:** IC3 BEC numerator ÷ Singapore business-population denominator
  (SingStat) for the frequency floor; SPF/CSA Singapore BEC/scam prevalence for likely/max;
  IC3/DBIR median for impact.min; a documented SG/APAC funds-transfer-fraud loss for impact.max.

### Objective 7 — `au_finance_bec_midmarket` → source-backed (4/6 → 6/6)  ✅ DONE 2026-07-20
**Result:** 6/6 source-backed. `frequency.likely` 0.21 (ABS 2024-25 all-cyber incident
prevalence), `frequency.max` 0.81 (MYOB/Dynata 2024 finance & insurance mid-sized cyber
prevalence). Calibration 0 warnings; Monte Carlo AVG AUD 124k / P95 350k / P99 524k.
**Notable consequence:** with BEC frequency now evidence-based, **BEC overtakes data breach
as the #1 ranked top risk** — consistent with real-world loss data (IC3/AFP/Coalition all
rank BEC/payment fraud first). Six test snapshots updated to match. Sources added:
`abs_characteristics_australian_business_2025`, `myob_business_monitor_cyber_2024`.

---

## Completed & merged

- **2026-07-20 — Objective 1:** `us_finance_bec_midmarket` 1/6 → **6/6 source-backed**.
  IC3÷Census freq floor, AFP 2025/2026 freq bridges, DBIR median floor, Coalition FTF stress.
  (PR #18, merged to `main`.)
- **2026-07-20 — Objective 2:** restored the 4 ritual owner docs; `/session:start` reads clean. (PR #21.)
- **2026-07-20 — Objective 3:** cut data-pack release `2026.07.20-us-bec-source-backed`
  (60 files, fp `074c78734932`). (PR #20.)

---

## Session log (append one line per phone session)

- 2026-07-19 — Queue designed during /session:start. Repo reality confirmed: clean tree,
  in sync with origin/main, Python 3.14.6. Objective 1 scoped to 5 approve-points.
- 2026-07-20 — Objective 1 completed (phone session, approve-each-anchor). US BEC shard
  1/6 → 6/6 source-backed. 4 new sources gathered, 5 evidence records added, calibration
  profile rewired, test count updated (IC3 7→8). All gates green.
- 2026-07-20 — Objectives 2 and 3 completed same session; all three PRs (#18/#21/#20)
  admin-merged to `main` after CI green (one CI catch: benchmark blocker count 62→47 from
  the calibration rewire, fixed). Queue repopulated with the P2 cycle (Objectives 4–7).
