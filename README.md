# 🔷 RiskShard

> **Every cyber risk estimate needs a most-likely loss. No public source publishes one.**
>
> Cyber loss figures get quoted far past what they can support, and nobody checks. There is no name
> for that job and no one doing it, so this is us doing it: reading the public reports everyone
> cites, one at a time, and writing down what each one actually publishes.
>
> **63 of 75 read. Zero publish a mode.**
>
> Every answer is pinned to a document hash with the passage quoted, so you can check us rather
> than trust us.

### ▶ [Read the audit](https://raviaxo.github.io/RiskShard/audit.html) · [Read the evidence](https://raviaxo.github.io/RiskShard/) — no install

## The four questions

Asked of every source, in the same words, so two people's answers can be compared.

| | plain | what we call it |
| --- | --- | --- |
| **1** | Does it tell you the **most likely** loss — not the average, the most likely? | mode |
| **2** | Does it show the **spread** of losses, or only one number? | distribution |
| **3** | Does it say **how often losses go bigger** than a given size? | exceedance |
| **4** | Can you tell **who was measured** — which countries, industries, sizes? | population |

Read on 62 sources so far, the answers are **0**, 14, 19 and 49. The first one is the finding.

**[Read the audit →](https://raviaxo.github.io/RiskShard/audit.html)** · or
**[read one source and send back four answers](https://github.com/raviaxo/RiskShard/issues/new?template=read_a_source.md)**
— about twenty minutes, nothing to install, and *"I could not tell"* is a real answer.

## Why this matters

A cyber loss figure travels a long way from the report that produced it. By the time it lands in a
board deck it has usually lost what it measured, who it measured, and what it can't bear. Nobody
puts those back, because that means reading the source, and reading the source is slow work nobody
is paid for. So the gap gets filled with the nearest available number.

**Four places that costs you something.**

**1 · You are about to cite a figure.** A risk register row, a board slide, an insurance
submission. Is "$4.9M average breach cost" an average of your kind of company? Does it bound
anything? Today you read the report or you don't. Here the answer is already written down with the
sentence quoted, including when the answer is that the source doesn't say.

**2 · You have to defend a number.** An auditor, a regulator, a CFO who doesn't believe you. Every
figure has an identifier pinned to a fixed release, and the citation carries the caveat, so the
limitation turns up in the room at the same time as the number.

**3 · You are buying or building risk tooling.** It will ask for min, likely and max, and compose
them as a beta-PERT where "likely" is the mode. No public source publishes a mode. So there is one
question worth asking any vendor: where did your most-likely number come from?

**4 · You publish loss figures yourself.** Vendor, researcher, statistics office, dataset
maintainer. The four questions are a labelling standard. Answer them and your figure can be used in
someone else's model. Don't, and it can only be quoted. This is the part that outlives the project,
and it is what [the roadmap](docs/ROADMAP.md) is pointed at.

**What this is not.** Not a prediction, not a benchmark to adopt unread, not a methodology. A shard
describes a *cell*, never a company. The simulation on each item is there because composing anchors
is what exposes their defects, not because the output is the offer.

**[Where this is going →](docs/ROADMAP.md)** — five milestones, four of them counts, and a decision
date already committed in writing.

## What RiskShard is — and isn't

**It is** a governed evidence object: a public figure carrying the label a
practitioner needs to decide whether it belongs in *their* model — what was observed,
who it was observed on, when, how it was measured, what statistical role it really
has, and what it can't end up supporting ([ADR-0010](docs/adr/0010-where-riskshard-stops.md)).

**It isn't** portable, and that is not a caveat — it is the finding. An org's controls,
threat environment, dependencies and time horizon are part of the thing being estimated,
so nothing travels intact. What we can do is label an observation well enough that you
can judge whether it travels to you. Fit is exposed as separate **facets** — geography,
sector, size, measurement basis — never a single score, because only you know which
mismatch matters for your scenario ([ADR-0011](docs/adr/0011-fit-is-a-facet-set.md)).

**The simulation is a reference rendering, not the product.** RiskShard stops at
governed evidence with its limits declared; quantification is your step. The engine is
kept because it is the mechanism that finds our own defects — every finding below exists
because something composes these anchors into a distribution and the result could be
inspected. It is never offered as the thing being sold.

**And it isn't finished.** A shard that clears the automated gate is a *review
candidate*, never "benchmark-grade" — that stays a recorded human decision.

## What we found in our own numbers

The point of governing evidence is that it lets you measure your own defects. These are
ours, each derived mechanically and re-runnable, and each published before anyone asked:

- **None of the 11 `impact.likely` anchors is a calibrated mode**, though the sampler
  treats it as one — and no value in the 18-entry measurement vocabulary denotes a mode,
  so the schema could not express one. **8** carry a published mean or median instead;
  **7** use a central tendency as a floor, which is not a lower bound on loss.
- **4 of 22 parameter families are coherent.** The other 18 compose anchors that measure
  different quantities, each validly sourced, none a reading of the same thing.
- **5 of 11 impact maxima carry no exceedance probability.** They say a loss this size
  happened, not how often a loss is worse. *(Was 7. Two were retired in v0.9.0 by finding
  the exceedance in a source we had already cited for a year — it was there and we had not
  read it.)*
- **Two published figures retracted** because they appear in no primary source, and **two
  claims withdrawn** after measurement contradicted them — including one asserted in
  writing to a dataset maintainer before it was checked.

And one that is not about us:

- **Zero of 58 public cyber-loss sources publish a mode.** Every three-point estimate
  composes as a beta-PERT whose middle parameter is the mode — the most probable single
  value, and the number the output is most sensitive to. No source read publishes one: not
  the national statistics offices, not the police reporting bodies, not the insurers. IBM's
  *Cost of a Data Breach* uses "average" 75 times and "median" zero times. **The industry
  standardised on a shape its evidence base does not produce**, and what goes in the slot is
  a published mean. [The audit →](docs/FINDINGS.md#1--no-anchor-we-hold-is-a-mode-and-the-schema-cannot-express-one)

  The same reading found the opposite of what we expected everywhere else: Cyentia publishes
  full loss distributions, DSIT states the cost of the top 5% of UK cases, Sophos states what
  share of ransom payments passed $5M. Every answer is pinned to a document hash with the
  passage quoted, and **the coverage is published beside the claim — 58 read, 14 held only as
  a landing page**, because a count without its denominator is how you get quoted wrong.

None of this says the sources are wrong, and none of it says the outputs are too high or
too low — a shard describes a *cell*, not a company, so "too high" has no referent.

**[Read the findings in full →](docs/FINDINGS.md)** — each one derived mechanically by a
named tool, re-runnable, with the corrections at the same volume as the results.

## The question RiskShard answers

> Given my geography, industry, company size, and threat concern: what public evidence
> exists, what does each figure actually measure, how far is it from my context, and
> what can it not be made to support?

**One decision, made out loud:**
[How much ransomware cover should an Australian mid-market financial firm buy?](docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md)
— the model, the seed, the exceedance table, the recommendation, and the reason the
obvious answer is wrong. It is also where the governance layer stops being bookkeeping:
the shard's `impact.max` is one company's disclosed loss with no exceedance probability
attached, and swapping it alone moves the chance a single event exceeds AUD 20M from
0% to 23%. The limit decision is a decision about that one anchor.

## Try it in one command

```bash
git clone https://github.com/raviaxo/RiskShard.git && cd RiskShard
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt   # Python 3.9+
python scripts/riskshard_console.py
riskshard> demo
```

`demo` runs the whole first-run path automatically on a real shard: select ->
inspect the trust boundary -> simulate -> explain -> export a report -> show the
next gap. Every step is a real command you can also type yourself.

Prefer a single non-interactive command? This runs the same demo end to end and
prints the sourced numbers, confidence, and honest caveats — nothing to type,
so you can verify the "every number is traceable" claim in one shot:

```bash
printf 'demo\nexit\n' | python scripts/riskshard_console.py
```

## Honest status

RiskShard is a working practitioner beta, not a finished product. Shards are
labeled by maturity: `governed_starter`, automated `benchmark_candidate`, and —
only after a recorded human review decision — benchmark-grade. "Automated
benchmark-ready" is never the same as "human-approved benchmark-grade," and the
distinction stays visible everywhere results appear.
## Progress over time

Data strength is tracked, not asserted. Each data-pack release records a snapshot
to the [progress ledger](docs/internal/strength_ledger.json); the table below is
regenerated with `python scripts/strength_ledger.py markdown` and shows how many
model parameters trace to a reviewed public source over time.

<!-- strength-ledger:begin (regenerate with: python scripts/strength_ledger.py markdown) -->
| Release | Date | Source-backed params | Cell-matched | Shards 6/6 | Bridged/est. |
| --- | --- | --- | --- | --- | --- |
| 2026.08.21 | 2026-08-21 | 66 / 66 | 7 | 11 / 11 | 0 |
| 2026.08.16 | 2026-08-16 | 66 / 66 | 7 | 11 / 11 | 0 |
| 2026.08.15 | 2026-08-15 | 66 / 66 | 7 (-24) | 11 / 11 | 0 |
| 2026.08.13 | 2026-08-13 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.08 | 2026-08-08 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.07 | 2026-08-07 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.03 | 2026-08-03 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.02 | 2026-08-02 | 66 / 66 | 31 (+3) | 11 / 11 | 0 |
| 2026.08.01 | 2026-08-01 | 66 / 66 | 28 | 11 / 11 | 0 |
| 2026.07.24 | 2026-07-24 | 66 / 66 (+2) | — | 11 / 11 (+1) | 0 (-2) |
| 2026.07.24 | 2026-07-24 | 64 / 66 | — | 10 / 11 | 2 |

**2026.08.21-v0.10.0 —** Cell-matched and bridged are unchanged. What moved is the audit: 58 of 72 sources read becomes 62 of 75, after the Japan NPA workbook turned out to be unread rather than unreadable and Sophos 2026 arrived. No published parameter value moved in this release.

**2026.08.16-v0.9.0 —** the two new modeled quantiles are the first this portfolio has held, and no value moved to produce them - the DE and JP manufacturing maxima kept their $5,000,000 anchor and gained the share above it that Sophos had published all along. Read a falling none_known count here as reading catching up with the corpus, not as new evidence arriving.

**2026.08.15-v0.8.0 —** the fall in *cell-matched* is the measurement getting honest, not the evidence getting worse. Not one parameter, source, value or caveat changed in this release. *Cell-matched* stopped being a field an author maintained by hand and became a value computed from each record's declared population against the shard's cell. The old field disagreed with those declarations on 45 of 66 cards, counting the same wildcard declaration as borrowed 28 times and as matched 72. **7 is what the number always was**; 31 was the count of a field that was not being kept. See [finding 6](docs/FINDINGS.md) and [ADR-0013](docs/adr/0013-fit-is-derived-not-stored.md).

**2026.07.24 (2026-07-24) —** Records a real strength change (JP shard closed: 64->66 source-backed params, 10->11 shards at 6/6) for which no data-pack release was cut. Kept because the improvement is real; it predates the release-version rule.
<!-- strength-ledger:end -->

A parameter moves from *bridged/estimated* to *source-backed* only through a
recorded evidence decision — so a rising source-backed count is real strengthening,
not relabeling.

**A count here can move for two different reasons, and the table cannot tell them
apart on its own: the evidence changed, or the way we measure it changed.** So a
falling number is not automatically bad news and a rising one is not automatically
good. Releases where the measurement itself changed carry a note above, recorded with
the entry rather than written beside it — 2026.08.15 is one, and it is the reason
*cell-matched* reads 7 where the prior release read 31.
## See the proof

**Challenge any number.** Every parameter answers *where did this come from?* before you
are asked. `challenge <parameter>` in the console (or
`python scripts/riskshard_modules.py provenance <shard> <parameter>`) prints the value,
the named source, the exact cited line, and the caveat in one look:

```text
frequency.max = 0.69 annual_probability   [source_backed · confidence medium]
  Source : Cyber Security Breaches Survey 2025/2026 (official_statistics, 2026-04-30)
  Quote  : ...large businesses experienced cyber breaches or attacks at 69%.
  Caveat : ...larger-organization prevalence may overstate mid-market frequency.
```

Disagree? `provenance <shard> --dispute <parameter>` prints a pre-filled GitHub issue URL,
so a skeptic becomes a contributor in one click.

**Every figure is citable, and the citation carries the caveat.** The pinned form names an
immutable, fingerprinted release — `RS:us_finance_bec_midmarket/impact.likely@2026.07.21-v0.1.0-stable`
— so a number quoted in a board deck still resolves to what it said when it was written.
Identifiers are never reused or deleted. Worked examples in [docs/CITING.md](docs/CITING.md);
the design is [ADR-0004](docs/adr/0004-citable-parameter-identifiers.md).

**Three things worth opening:**

- [**A decision made out loud**](docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) — how much
  ransomware cover an Australian mid-market financial firm should buy, including why the
  obvious answer is wrong. Swapping one anchor moves the chance a single event exceeds
  AUD 20M from 0% to 23%; the limit decision *is* a decision about that anchor.
- [**Every parameter, with its source and caveat**](docs/EVIDENCE_REPORT.md) — regenerated
  with `python scripts/riskshard_modules.py provenance --all`.
- [**A worked contribution, source to preflight**](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md) — one
  real accepted change end to end, with the limitations made *louder*, not quieter.

## Documentation

Start with [docs/README.md](docs/README.md).

- [docs/FINDINGS.md](docs/FINDINGS.md) — what governing this evidence turned up, including
  what we got wrong.
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the model, its limits, and the accountability stance.
- [docs/BASIS_OF_PREPARATION.md](docs/BASIS_OF_PREPARATION.md) — how to read a figure: fit,
  mixed ranges, exceedance, and why a maximum is not a bound.
- [docs/REFERENCE.md](docs/REFERENCE.md) — commands, file formats, repository layout, and how
  to run the engine.
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute, including the DCO sign-off.
- [docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md) — a source taken
  end-to-end to a passing contribution.
- [docs/adr/](docs/adr/) — architecture decision records; [the index](docs/adr/README.md)
  reads as the project's reasoning in order.

## License

Copyright (C) 2026 Sergio Alonso.

RiskShard is free software, licensed under the **GNU Affero General Public License
v3.0 (AGPL-3.0)**. You may use, study, share, and modify it under those terms; if
you run a modified version as a network service, the AGPL requires you to offer
that service's users the corresponding source. See [LICENSE](LICENSE).

Contributions are accepted under the same license via the Developer Certificate of
Origin (DCO) — sign off your commits with `git commit -s`. See
[CONTRIBUTING.md](CONTRIBUTING.md).
