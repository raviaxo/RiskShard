# Research scripts

One-off scripts that produced a finding recorded in an ADR or a pre-scout note. They are
**not product code**: not wired into the CLI, not covered by the test suite, and not
maintained. They are kept so a claim made from them can be re-run and checked.

- `edgar_sample.py` / `edgar_verify.py` — the Item 1.05 sampling behind
  [`../../adr/0005-documented-loss-event-registry.md`](../../adr/0005-documented-loss-event-registry.md).
  `edgar_sample.py` does loose proximity matching across 20 filers; `edgar_verify.py`
  re-checks the hits at sentence level. The difference between them (6 apparent hits vs 4
  real ones) is why the ADR requires verification-assisted extraction rather than
  automatic.
