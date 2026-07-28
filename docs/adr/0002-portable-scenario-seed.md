# ADR-0002 — Portable scenario seeds (machine-independent simulation)

- **Status:** Accepted
- **Date:** 2026-07-28
- **Deciders:** repo owner
- **Related:** [`../monte-carlo-determinism-architecture.md`](../monte-carlo-determinism-architecture.md),
  [`../../engine/fair_calc.py`](../../engine/fair_calc.py)

## Context and problem

`derive_scenario_seed()` mixed the scenario's **absolute filesystem path** into the
per-scenario RNG seed:

```python
payload = f"{base_seed}:{Path(scenario_path).as_posix()}:{fingerprint}"
```

The console passes an absolute path, so the derived seed — and therefore every draw —
was a function of where the repository happened to sit on disk. The same shard, the
same `seed 42`, and byte-identical evidence produced **different loss numbers on
different machines**:

| | local checkout (`/Users/…`) | CI checkout (`/home/runner/…`) |
|---|---|---|
| `au_finance_bec_midmarket` AVG | AUD 55,021.72 | AUD 54,820.66 |

Found 2026-07-28 by diffing a local explorer build against the CI-built page then live.
Every shard differed, by roughly 0.2–1.5%.

This contradicts the principle this project already committed to in
`docs/monte-carlo-determinism-architecture.md`:

> Audit trails must support third-party verification **without access to original
> execution environment.**

It also made `reproduction_command` — which the tool prints to users — unable to
reproduce a published number anywhere except the machine that produced it. Runs were
still deterministic *within* one checkout, so nothing was random; the numbers simply
were not portable, which is the property that matters for an evidence-governed tool.

## Decision

**Derive the per-scenario seed from a project-root-relative path**, not an absolute one.

```python
def portable_scenario_key(scenario_path, root=PROJECT_ROOT):
    """Machine-independent identity for a scenario file."""
    candidate = Path(scenario_path)
    try:
        return candidate.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return candidate.name
```

`scenarios/business_email_compromise.yaml` is the same string on every machine, so the
seed is too. Per-scenario RNG isolation is unchanged — distinct scenarios still get
distinct, independent streams; only the machine-dependence is removed.

A scenario stored **outside** the project root (an org-specific file elsewhere on disk)
falls back to its filename. Its directory is by definition user-specific, so including
it would reintroduce exactly the defect being fixed. The cost is that two out-of-tree
scenarios sharing a filename share a seed; they remain independently *simulated*, and
the tradeoff is recorded here rather than hidden.

## Consequences

**Every published loss number changes.** This is a one-time, deliberate churn:

- the explorer (`docs/index.html`) and its per-shard AVG/P95/P99
- any loss figure previously quoted publicly

The test suite turned out **not** to assert simulated values — it asserts currency
prefixes, the printed run receipt (`trials=10000, dist=pert, seed=42`) and structure,
not AVG/P95/P99 digits — so all 198 tests passed unchanged. That is a gap worth naming:
nothing in CI would have caught this defect, and nothing would catch a future regression
in the numbers either. Tracked as a follow-up (a golden-value test for one shard, which
only becomes safe to write *because* the seed is now portable).

Evidence, sources, cited lines, caveats, provenance, parameter values, the data-pack
fingerprint and the strength ledger are **untouched** — this changes how draws are
seeded, not what the evidence says. Shard grades and the maturity ladder are unaffected.

The churn is taken now, before new shards are added, so it happens once rather than
across a larger surface later.

## Alternatives considered

- **Drop the path entirely, seed from the scenario fingerprint alone.** Simpler and
  fully portable, but two scenarios with identical configs would share a stream. Keeping
  a stable path component preserves the existing isolation guarantee with a smaller
  behavioural change.
- **Seed from the module id.** Not available at this layer; `run_portfolio` works from
  scenario files, and threading module identity down would couple the simulator to the
  module registry.
- **Make report metadata paths portable too.** `metadata.input_path` and
  `reproducibility.scenarios[].path` still record absolute paths, so two machines produce
  reports that differ in those fields. That is noise in an audit artifact rather than a
  correctness defect, and it is deliberately out of scope here. Tracked as a follow-up.
