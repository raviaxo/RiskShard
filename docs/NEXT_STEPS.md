# NEXT_STEPS — active session queue

> Point Claude Code at this file to resume: **"Run /session:start, then resume Objective N from docs/NEXT_STEPS.md."**
> Drive mode for this queue: **approve each anchor** — Claude stops at every evidence
> decision (source trust, chosen value, caveat) and waits for a short yes / no / adjust.
> Designed to be driven from a phone: Claude fetches, extracts, drafts, and runs; the
> human only makes short approve/reject calls. No hand-editing of YAML required.

Planned 2026-07-19. Work the objectives **one at a time, in order.** Do not pull the
next objective into scope until the current one meets its Definition of Done.

---

## Objective 1 — Strengthen `us_finance_bec_midmarket` from 1/6 → source-backed  (repo P1)  ✅ DONE 2026-07-20

**Result:** shard is now **6/6 source-backed (medium confidence)**. All five approve-points landed:
`frequency.min` 0.004 (IC3 ÷ Census SUSB reported-complaint floor) · `frequency.likely` 0.63
(AFP 2025) · `frequency.max` 0.74 (AFP 2026) · `impact.min` $50k (DBIR 2026 median) ·
`impact.max` $6.4M (Coalition largest FTF loss). Calibration emits 0 warnings; Monte Carlo:
AVG $620k, P95 $1.67M, P99 $2.33M. validate/preflight/doctor/tests all pass. Caveats kept loud
in every record. Sources added: `census_susb_2022`, `afp_payments_fraud_2025/2026`,
`coalition_ftf_largest_clawback_2023`. Calibration profile rewired to the source-backed evidence.
Uncommitted pending review.

**Why:** Readiness dashboard P1 = "Replace assumptions for Business Email Compromise."
It is the weakest cell in the library: 1/6 source-backed, 5 bridged. Every data-breach
shard is already 6/6, so BEC frequency evidence is the library's soft spot.

**Current provenance (from `riskshard_modules.py packs us_finance_bec_midmarket`):**
- `impact.likely` — ✅ source-backed via `fbi_ic3_2025_report` (trust=high). Done.
- `frequency.min` / `frequency.likely` / `frequency.max` — assumption_only (low conf)
- `impact.min` — assumption_only
- `impact.max` — assumption_only

**The 5 approve-points (each is a stop-and-confirm from the phone):**
1. `frequency.min`  — denominator-derived US BEC floor rate
2. `frequency.likely` — denominator-derived US BEC central rate
3. `frequency.max`  — denominator-derived US BEC stress rate
4. `impact.min`     — IC3 loss-distribution floor anchor
5. `impact.max`     — IC3 / regulatory stress-loss anchor

**Method (reuse the golden-contributor pattern already proven for GB/AU):**
frequency = FBI IC3 2025 US BEC complaint count ÷ a US business-population denominator
(Census County Business Patterns / SBA firm counts for the finance sector, mid-market
band). This mirrors the "denominator-derived reported-breach frequency floor" GB/AU use.
Follow `docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md` end-to-end for each anchor:
`source → extraction → evidence → calibration → evidence pack → preflight`.

**Files it will touch:** `sources/registry.yaml`, `extractions/`, `evidence/`,
`calibrations/us_finance_business_email_compromise.yaml`, the `us_finance_bec_midmarket`
scenario/module, and `results/` (local, git-ignored).

**Definition of Done:**
- `riskshard_modules.py coverage` shows `us_finance_bec_midmarket` as **source-backed** (6/6).
- `contributor_preflight.py` passes for the changed pack.
- `readiness_dashboard.py` P1 is cleared or advanced.
- Every new anchor keeps its caveats **louder, not quieter** (denominator assumptions,
  sector breadth, IC3 reporting bias). No benchmark-grade claim without a human decision.
- Committed with `-s` (DCO) on a branch; not pushed unless asked.

---

## Objective 2 — Restore the session-open ritual's owner docs  ✅ DONE 2026-07-20

**Result:** created `AGENTS.md`, `docs/PROJECT_STATUS.md`, `docs/HANDOVER_STOPPING_POINT.md`,
`docs/PUBLISHABLE_REQUIREMENTS.md` (plus this `NEXT_STEPS.md`). All thin and cross-linked
per one-canonical-owner — they point to README/CONTRIBUTING/readiness rather than duplicate.
`/session:start` now reads cleanly: all five owner files exist, no broken relative links,
preflight + doctor pass.

**Why:** `/session:start` is load-bearing but its named docs do not exist:
`AGENTS.md`, `docs/HANDOVER_STOPPING_POINT.md`, `docs/PROJECT_STATUS.md`,
`docs/PUBLISHABLE_REQUIREMENTS.md` (this `NEXT_STEPS.md` is the first one restored).
Every future session — including phone sessions — currently boots blind.

**Scope (create, grounded in repo reality — draft, human approves each):**
- `AGENTS.md` — operating rules + definition of done (lift from the real workflow:
  DCO sign-off, caveats-louder rule, preflight gate, one-canonical-owner).
- `docs/PROJECT_STATUS.md` — current capabilities + known gaps (derive from README
  "What Works Today" / "In Progress" + the readiness dashboard, don't reinvent).
- `docs/HANDOVER_STOPPING_POINT.md` — a thin pointer that always names the current
  top blocker and restart point (this file's active objective).
- `docs/PUBLISHABLE_REQUIREMENTS.md` — the public-surface bar + change-control note
  (nothing public that couldn't be shown to a CISO; strategic decisions need an owner doc).

**Definition of Done:** `/session:start` reads cleanly with zero missing-file errors.
Docs point to each other without duplicating (respect one-canonical-owner).

---

## Objective 3 — Cut a named data-pack release  (repo P3)

**Why:** Readiness dashboard P3 = "Cut a named data-pack release (release discipline)."
Current data pack: `2026.07.19 2b74665387b2 files=60`. Mostly mechanical; good phone closer.

**Method:** `riskshard-data-pack` / `scripts/` release path; verify with
`riskshard-package-smoke`. Tag and record the release fingerprint.

**Definition of Done:** a named, fingerprinted data-pack release exists; package smoke
passes; release is recorded where the repo records releases (`data_pack_releases/` / `release/`).

---

## Session log (append one line per phone session)

- 2026-07-19 — Queue designed during /session:start. Repo reality confirmed: clean tree,
  in sync with origin/main, Python 3.14.6. Objective 1 scoped to 5 approve-points.
- 2026-07-20 — Objective 1 completed (phone session, approve-each-anchor). US BEC shard
  1/6 → 6/6 source-backed. 4 new sources gathered, 5 evidence records added, calibration
  profile rewired, test count updated (IC3 7→8). All gates green. Awaiting commit decision.
  Next: Objective 2 (restore ritual owner docs).
