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
- `edgar_corpus_census.py` — the three-lane census behind
  [`../edgar_corpus_census.md`](../edgar_corpus_census.md), which sizes the ADR-0005
  registry decision. Supersedes `edgar_sample.py` as the discovery method: matching
  periodic reports directly on cost phrases reaches roughly three times as many issuers as
  following Item 1.05 filings, because the cost lands quarters after the incident and often
  with no 8-K at all. Run `discover` → `quantify` → `report`; results cache under
  `$EDGAR_CACHE` (default: a temp directory), so re-runs are cheap.
