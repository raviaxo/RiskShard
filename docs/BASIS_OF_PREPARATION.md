# Basis of preparation

*How to read a figure on the [explorer](https://raviaxo.github.io/RiskShard/) and in the data pack.
This page holds the full basis; the explorer carries a short version and links here. Moved off the
front page on 2026-08-19, when the front page was measured at 1,676 words of prose before the first
item rendered.*

## The run

Monte Carlo, 10,000 trials, seed 42, machine-independent seeding — a modeled range from public
evidence, not a prediction. A parameter marked **estimate** is an interpretive value whose
limitation is stated on its face; every other parameter cites a named public source.

Grades follow the maturity ladder: `governed_starter` → `benchmark_review_candidate` →
benchmark-grade. The last requires a recorded human review and **no item currently holds it.**

## Declared-for and fit are two different lines, and the order is deliberate

**`declared for`** is the population the source measured — countries, industries, size bands,
threats. It is a property of the record and it is true for every reader.

**`fit`** is *computed* from that population against the item's own cell, which the line always
names. It tells you how the record sits relative to our target and almost nothing about yours. It
is stored nowhere ([ADR-0013](adr/0013-fit-is-derived-not-stored.md)).

A parameter marked **bridged** is source-backed by evidence not drawn from the item's own cell. The
dimensions borrowed across are named on the fit line, and that chip is what the cell-matched /
bridged counts tally. Bridging is declared, never hidden: a reader counting the source-backed total
should not infer more cell-specific evidence than exists.

### That the first line means what it says is a repair, not an assumption

On **2026-08-14**, **21 records** were found declaring the cell they were borrowed *for* rather than
the population measured — the US BEC frequency floor declaring financial-services mid-market over an
economy-wide numerator and denominator; three US data-breach frequencies declaring `US` over a UK
survey; two Singapore anchors declaring `SG` over US data. All 21 were corrected, **no published
figure moved**, and a test now fails the build if another appears.

### The cell-matched count got much worse on 2026-08-15, and that is the correction

Fit used to be a second field an author maintained by hand beside the declaration. Measured against
those declarations it **disagreed on 45 of 66 parameters**, counting the same all-industry
declaration as borrowed 28 times and as matched 72.

It was retired. Fit is now computed on one rule for every facet — bridged when the declared
population does not name this cell's value — so cell-matched fell **31 → 7** and bridged rose
**35 → 59**. **No published figure moved**; every value, source, caveat and simulated total is
unchanged. **7 is what the number always was.**

One consequence is worth knowing while reading: a statutory penalty cap, a documented single-event
loss and a same-survey adjacent band are all measured over some other population, so they now read
*bridged* too. The `measures` line is what tells you which of those a parameter is.

### No fit score, ever

This project publishes no fit score, grade or percentage, and will not. Compressing these facets
into one number would assert that a geography mismatch and a size mismatch trade off against each
other in a way we cannot know for your scenario — a geography mismatch is fatal to one analysis and
irrelevant to the next. The facets are listed separately so you decide which ones bite.
See [ADR-0011](adr/0011-fit-is-a-facet-set.md).

## What a parameter measures, and mixed ranges

Each parameter states *what quantity it measures* on its `measures` line. This is independent of the
source and of the population: two anchors can both be drawn from the item's own cell and still
measure different things — an annual breach prevalence against an event frequency, or a perceived
cost against an average total loss against a regulatory penalty.

Where a range's minimum, likely and maximum do not share one basis it is marked **a mixed range**
above that item's table, with the differing bases named. A mixed range is **not** an error and
nothing is hidden because of it — each figure remains separately sourced — but the width between the
anchors is then partly a difference of *definition* rather than of uncertainty, and a reader should
not treat it as a spread.

This declaration was added after a practitioner asked the question in the open. Which mixes are
acceptable is not yet settled and is recorded in
[`OPEN_JUDGMENT_CALLS.md`](OPEN_JUDGMENT_CALLS.md), not decided quietly.

## A maximum is not a bound

Each item's `impact.max` also states what is known about it *being exceeded*, on its `exceedance`
line.

Most say **none known**, and that is the honest answer rather than an omission: published loss
distributions carrying tail quantiles are rare and mostly commercial, so nearly every public maximum
is one documented event, the largest row in someone's dataset, or a legal ceiling. Read those as
**the largest loss found**, never **the largest loss that can happen** — a figure with no exceedance
statement says a loss that size occurred, not how often a loss is worse.

Where an exceedance *can* be stated the line gives it. The rate shown is a within-sample rate on
insured claims, which is **a floor**: losses above it are more common than the sample says, not less.

### The maximum drives the average rather than capping it

Because the model composes minimum, likely and maximum into one distribution, the maximum's share of
the modeled average can be computed exactly — no sampling, no seed, no error term. Where that share
exceeds half, the item says so directly under its loss figure.

Read it together with the item's `exceedance` line: **a figure mostly produced by an anchor that
admits no exceedance probability is a figure resting on one observation**, however carefully that
observation was sourced. The maximum is simultaneously the least evidenced anchor and the one the
result is most sensitive to.

Run `python scripts/riskshard_modules.py tail` for the full table, including what each item's annual
average does when only the maximum is moved.
