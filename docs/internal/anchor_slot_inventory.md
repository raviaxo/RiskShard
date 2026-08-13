# Anchor-slot inventory — scoping the mis-specification fix

*Internal working doc (governed by [`../../AGENTS.md`](../../AGENTS.md)). Produced 2026-08-12 to
size the correctness objective before any data changes. The queue owner is
[`NEXT_STEPS.md`](NEXT_STEPS.md); this file is the measurement behind one of its entries.*

> **✅ ACTED ON 2026-08-13 — "declare, don't invent" shipped.** All 15 central-tendency anchors
> (8 at `likely`, 7 at `min`) carry a written slot declaration in their calibration `rationale`,
> and the declaration is **derived** rather than hand-maintained (`engine/slot_roles.py`),
> appearing per-anchor in the evidence report and on every shard in the explorer.
> **No published number moved** — all 11 shards' AVG/P95/P99 are byte-identical, which is what
> a declaration-only fix must do.
>
> **One finding this file did not have.** The dead end is worse than "no source we hold offers a
> mode": **no value in the 18-entry `measurement_basis` vocabulary denotes a mode at all**, so
> the schema could not express one if a source published it. That makes the mode-slot statement
> structural rather than per-shard — **all 11 `impact.likely` anchors** are something other than
> a calibrated mode, of which the 8 central-tendency ones are the sharper case. Both counts are
> pinned in `tests/test_slot_roles.py`.
>
> The optional source check ran and returned the expected documented negative: NetDiligence 2025
> reports averages and Verizon DBIR 2026 carries no loss median in prose. Neither yields a mode.

## Method

Every `evidence_id` referenced by every calibration profile was resolved mechanically to its
evidence record and that record's `measurement_basis` — 90 anchor rows across 15 calibration
profiles, 0 unresolved. The 15 profiles were then restricted to the **11 risk-module shards**
(`risk_modules/*.yaml` → its `calibration:` key); the other 4 profiles are drift-watch top-risk
scenarios and are not part of any published shard count.

`transform` was checked separately and does not affect the classification: every impact anchor is
`direct` or `currency_convert`, and a currency-converted mean is still a mean.

## The correction this produced

**The published mode-slot count was wrong.** It read *7 of 11* and it is **8 of 11**. The other
two counts on the same list reproduced exactly (floor 7 of 11, both 6 of 11), which is what makes
the outlier credible rather than a methodology difference.

The two shards carrying a mean at `likely` **only** — `gb_finance_data_breach_midmarket` and
`us_finance_data_breach_midmarket` — are the likely mechanism of the original error: six shards do
both, and adding just one of these two reads as seven.

**The defect is one shard worse than published, not better.** Corrected in
[ADR-0009](../adr/0009-what-riskshard-is-and-is-not.md),
[ADR-0010](../adr/0010-where-riskshard-stops.md) and `NEXT_STEPS.md`. The count was also stated to
John Flack in GRC EC on 2026-08-11 and is owed a correction there — owner's call, not the repo's.

## The inventory

| shard | `impact.min` | `impact.likely` | `impact.max` | class |
| --- | --- | --- | --- | --- |
| `au_finance_bec_midmarket` | mean_total_event_cost | **mean_total_event_cost** | single_documented_event_loss | **A** |
| `au_finance_data_breach_midmarket` | mean_total_event_cost | **mean_total_event_cost** | statutory_penalty_cap | **A** |
| `ca_finance_data_breach_midmarket` | mean_total_event_cost | **mean_total_event_cost** | observed_extremum | **A** |
| `fr_finance_data_breach_midmarket` | mean_total_event_cost | **mean_total_event_cost** | statutory_penalty_cap | **A** |
| `sg_finance_bec_midmarket` | median_total_event_cost | **mean_total_event_cost** | single_documented_event_loss | **A** |
| `us_finance_bec_midmarket` | median_total_event_cost | **mean_total_event_cost** | single_documented_event_loss | **A** |
| `gb_finance_data_breach_midmarket` | perceived_cost_self_reported | **mean_total_event_cost** | regulatory_penalty_issued | **B** |
| `us_finance_data_breach_midmarket` | cost_component | **mean_total_event_cost** | observed_extremum | **B** |
| `au_finance_ransomware_midmarket` | mean_total_event_cost | cost_component | single_documented_event_loss | **C** |
| `de_industrial_ransomware_midmarket` | cost_component | cost_component | observed_extremum | **D** |
| `jp_manufacturing_ransomware_midmarket` | cost_component | cost_component | observed_extremum | **D** |

### Class A — central tendency at both `min` and `likely` (6 shards)

Two central-tendency statistics, ordered by magnitude, labelled as a floor and a mode. This is
John Flack's complaint verbatim: *"they don't automatically become 'min' and 'likely' because one
happens to be smaller."* Four are mean→mean; two (`sg_bec`, `us_bec`) are median→mean.

The median→mean pair is the **most** defensible of the six and still wrong: a median and a mean of
a right-skewed loss distribution are at least two different statistics of one population, ordered
the way skew predicts. They are still not a minimum and a mode. This is exactly the pairing
[ADR-0007](../adr/0007-construct-coherence.md) open question 1 asks about.

### Class B — central tendency at `likely` only (2 shards)

Floor is defensible (`perceived_cost_self_reported`, `cost_component`); the mode slot is a
published mean. These two are the shards missing from the original count.

### Class C — central tendency at `min` only (1 shard)

`au_finance_ransomware_midmarket` has a mean at the floor and a cost component at `likely`.

### Class D — no central-tendency defect, different problem (2 shards)

`de` and `jp` are clean on *this* axis: no mean occupies a slot. Both instead run
`cost_component` → `cost_component`, i.e. a component of loss (ransomware recovery cost) standing
in for total event impact across two slots. **That is an ADR-0007 coherence issue, not a slot
issue, and it is out of scope for this objective** — recorded here so the inventory is not later
read as "these two are fine."

## Is any of it reassignable?

The cheap repair would be to swap in a mode-like statistic already extracted from the same source.
**It does not exist.** For each of the 8 mode-slot anchors, every other `measurement_basis` we
hold from that same source:

| shard | source | other bases we hold from it |
| --- | --- | --- |
| `au_bec`, `us_bec` | `fbi_ic3_2025_report` | context_statistic · mean_total_event_cost · reported_case_rate |
| `au_data_breach` | `securitybrief_ibm_au_breach_costs_2026` | *none* |
| `ca_data_breach` | `ibm_canada_cost_data_breach_2025` | *none* |
| `fr_data_breach` | `ibm_france_cost_data_breach_2025` | *none* |
| `gb_data_breach` | `ibm_cost_data_breach_uk_2025` | context_statistic |
| `sg_bec` | `spf_annual_scam_cybercrime_brief_2025` | reported_case_rate |
| `us_data_breach` | `netdiligence_cyber_claims_2025` | cost_component · mean_total_event_cost · observed_extremum |

**Not one mode, and nothing convertible into one.** Reassignment from existing extractions is a
dead end for all 8.

What remains unknown is whether the *source documents* publish something mode-like we never
extracted. Two are worth one look each and no more — NetDiligence publishes median claim severity
alongside the mean, and Verizon DBIR publishes loss percentiles for BEC — and the honest expected
outcome is a **documented negative** for IBM, which publishes an average and no distribution.

## Recommendation

**Declare, do not invent.** The cheapest honest option in `NEXT_STEPS` survives contact with the
inventory and is now the *only* option supported by the data: state on the record that `likely` is
a **published central-tendency statistic, not a calibrated mode**, and that the engine composes it
as though it were one. That is true of all 8, costs no invented data, and is in the repo's idiom.

Manufacturing a mode nobody measured would be the withdrawn "numbers are inflated" claim in a new
costume — a directional change to published figures with no observable target to justify it.

Scope discipline per [ADR-0009](../adr/0009-what-riskshard-is-and-is-not.md): no fourth axis. The
"why does this number occupy this slot" answer goes in the per-parameter calibration `rationale` as
prose. **Do not predict which way corrected numbers move** — this fix should not move any published
number at all, which is itself the argument for doing it.

## Reproducing this

The measurement is mechanical and should be re-runnable rather than trusted. Nothing here was read
off by eye; if this inventory is ever cited, regenerate it first — the count in this very file
replaced a hand-made one that was wrong by one shard.
