# Amount shape and accounting treatment — design input from John Flack, and what it costs

*Received 2026-08-16 in GRC EC `#labs_demos`. Measured the same day. **Not yet built** — three
things need resolving first and one of them needs him.*

## What he proposed

After reading [ADR-0012](../adr/0012-loss-event-registry-bounded-trial.md)'s constraints he accepted
that the schema structurally prevents registry entries becoming parameters — his litmus test —
and then made a design argument. Verbatim in substance:

- **Both `range` and `accrual`, because they are independent.** *"Range tells me how the disclosed
  amount was expressed, and accrual tells me something about its accounting status … so a filing
  could disclose a $10–15M estimated range, a $12M accrual, or even both, and those aren't
  interchangeable."*
- **Generalise beyond range to an amount *shape*:** `point / bounded range / lower bound / upper
  bound / unquantified` — *"preserving the source values rather than coercing them into a point."*
- **Keep accounting treatment as a separate facet:** `accrued / incurred-realized /
  estimated-provisional / recovery`.
- **The rationale:** *"preserve what the filing asserts instead of normalizing / 'sanding off'
  information because a downstream model would prefer one, pretty number."*

## Why the orthogonality catch is right

Adding `range` as an amount **type**, next to `direct_cost` and `insurance_recovery`, would have
conflated **what the number is** with **how it was expressed**. Those vary independently, and his
example proves it in one line. This is a category error we would have shipped.

## What the corpus actually exercises, and why the number is misleading

Measured over the 36 events / 48 amounts held today:

| | count |
| --- | ---: |
| cited line expressing a **range** | **3** |
| mentioning an **accrual** | **1** |
| mentioning an estimate | 7 |
| saying **not estimable** | **0** |

**Do not read 3-and-1 as weak justification.** Extraction only ever admitted amounts that could be
coerced into a point, so a filing disclosing *only* a range, or saying *"material but not yet
reasonably estimable"*, would have been dropped at extraction **because the schema could not hold
it**. ADR-0012's census recorded 38 surviving issuers against only ~33 with a "directly usable"
figure; that gap is where these live.

The item with **zero** current usage — `unquantified` — is plausibly the most valuable of the five,
and it measures as least valuable for exactly the reason it is needed.

## Three things to resolve before building

**1. `recovery` collides across the two facets, and this is the real question.** We hold
`insurance_recovery` as an amount **type** (10 of 48 amounts). He places recovery in **treatment**.
It is genuinely both — a distinct quantity *and* an accounting posture. Moving it breaks 10 records;
duplicating it invites two fields disagreeing. **He wrote the proposal without seeing our schema, so
this is worth asking him rather than guessing.**

**2. The treatment facet partly duplicates our existing `status`.** We already carry
`provisional | final | not_stated`. His `estimated/provisional` and `incurred/realized` are a richer
cut of the same axis, so this is a **refactor of a populated field**, not a clean addition — all 48
amounts get remapped.

**3. `shape` is the only clean addition.** Nothing in the schema expresses it today.

## Standing constraints this must respect

- **It is a schema change → Change Control → needs its own ADR** before code moves.
- **[ADR-0016](../adr/0016-the-audit-is-the-product.md) makes the audit the only growth surface.**
  This is defensible as a *schema correction* — the labelling standard is the product, and getting
  the amount shape right is a contribution whether or not the registry survives. It is **not**
  defensible as registry expansion, and the framing matters.
- ⚠️ **This does not move either ADR-0012 metric.** It is a design input, not a contributed entry
  and not a citation. It is now easier to fudge that than it was yesterday, because he has engaged
  substantively. [ADR-0017](../adr/0017-the-kill-criterion-gets-a-clock.md) settles it: the metrics
  do not move.
- ⚠️ **Improving the registry weeks before a criterion that may retire it invites sunk-cost
  reasoning.** *"We just improved it"* is not an argument at the measurement point.

## Recommended next action

**Reply to him with the `recovery` question specifically** — does an insurance recovery stay a
distinct quantity, or become a treatment of one? That is the single place his design meets our
existing records, and he will have a view. Then write the ADR against his answer rather than
against a guess.
