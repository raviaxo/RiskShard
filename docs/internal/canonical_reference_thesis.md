# What would make RiskShard canonical (2026-07-28)

*Internal strategy note. Written because the question — what makes this the place people
have to go for something nobody else provides — was being answered in conversation and
kept getting lost. Governed by [`../../AGENTS.md`](../../AGENTS.md); it records reasoning
and a falsifiable test, not a plan of record.*

## The reference class

CVE, MITRE ATT&CK, Have I Been Pwned. None of them won on data quality.

- **ATT&CK** became the shared **vocabulary**. The value is not the technique write-ups,
  it is that everyone agreed to use the same names, so reports and tools interoperate.
- **CVE** became an **identifier authority**. The value *is* the ID — an unambiguous
  handle two parties can use years apart.
- **HIBP** had a genuinely unique corpus *and* a neutral operator nobody suspected of
  selling them something.

The pattern: each became **the thing you cite**, not the thing you use. That is a
different win condition from "people use the tool", and it changes what to build.

## The constraint to be honest about

**RiskShard will never have the best data.** Insurers and brokers already hold real
per-claim loss distributions — Coalition, Chubb, Munich Re, Verisk. They do not publish
them because the data *is* the business. No amount of open-source effort closes that gap.

So "data nobody else has" is not an available strategy. What is available is structural:

> **A vendor cannot publish its caveats.**

A commercial benchmark provider cannot write "this figure rests on a bridge that overstates
by an unknown factor" — it would undermine the sale. This project published its weakest
number as a feature. That asymmetry is not a head start; it is a property competitors
cannot copy without damaging themselves.

**The honest formulation: RiskShard will never have the best numbers. It can have the
only auditable ones.**

## The thing nobody else gives

Everyone supplies numbers. Nobody supplies **a number with its argument attached** — the
cited line, the caveat, the derivation, *and a public record of who challenged it and what
happened as a result*.

The recurring painful moment in GRC is not modelling. It is **defending**: an auditor, a
regulator, or a CFO pushes back, and the honest answer today is "a vendor report I cannot
share and did not verify." That moment recurs constantly, is currently unanswerable, and
is the moment to own completely.

## What follows concretely

1. **Citable identifiers with permanence guarantees** — see
   [`../adr/0004-citable-parameter-identifiers.md`](../adr/0004-citable-parameter-identifiers.md).
   Two prerequisites already exist: reproducibility (ADR-0002) and fingerprinted immutable
   releases.
2. **Public dispute *outcomes*, not just dispute intake.** The dispute button creates
   issues; nothing shows what happened. "This value was challenged twice — here is what
   changed and why" is something no vendor will ever publish. Probably the single most
   differentiated thing buildable here, and mostly a presentation problem since the
   history is already in GitHub.
3. **Named contributor attribution per parameter.** ATT&CK grew because contributing
   conferred status. A name on the parameter someone sourced turns contribution into a
   credential.
4. **The caveat travels inside the citation** (ADR-0004's cite-this format), so a number
   quoted in a board deck carries its limitation with it.

## The metric

Stars and traffic are the wrong measure. The falsifiable one:

> **Does a RiskShard parameter identifier appear in a document written by someone else?**

A board deck, an audit workpaper, a regulatory filing, a paper. The first external
citation is the moment this stops being a project and starts being a reference.

## How this fails

Two risks, both testable inside 12 months:

- **The population may be too small.** ATT&CK served a large existing group that needed a
  shared vocabulary. "People who quantify cyber risk in dollars and get challenged on it"
  may not be numerous enough to sustain a canonical resource.
- **A commons needs contributors.** If the maintainer is still the only source of shards
  in a year, this is a portfolio, not a commons, and the thesis does not hold.

## Consequence for breadth vs depth

This tilts the open question in
[`coverage_harvest.md`](coverage_harvest.md). Citability rewards **depth and permanence**:
a parameter someone cites must survive being attacked. Coverage only helps once someone
can find their own cell. That argues for depth-first, with **identifier infrastructure
sequenced ahead of shard count** — a large portfolio without stable identifiers is harder
to retrofit than a small one.
