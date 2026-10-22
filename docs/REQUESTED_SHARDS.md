# Requested shards

What the community wants quantified next. This is RiskShard's demand signal: each row
is a country × sector × threat someone asked to see modeled.

## Read this first — a request does not currently produce a shard

**Shard coverage is frozen at 11 cells.** [ADR-0016](adr/0016-the-audit-is-the-product.md)
part 2 froze it, and [ADR-0006](adr/0006-depth-over-breadth.md)'s amendment of 2026-08-22
withdrew demand as grounds to reopen it: *"ADR-0016 part 1 declines a new cell however it
arrives, and `docs/REQUESTED_SHARDS.md` is no longer a route to one."* Two triggers do
reopen breadth — a second maintainer, or genuinely per-cell impact evidence — and demand
is not one of them.

**Requests are still recorded and published here**, because a recorded request is evidence
about what this corpus is missing and that evidence keeps whether or not the freeze lifts.
What changed is the promise: this page said until 2026-09-29 that *"repeated or strong
requests become the next objective in the internal queue,"* which had been false since the
2026-08-22 amendment. Asking tells us where the gap is. It does not get filled.

## How to request one

Open the **[Request a shard](https://github.com/raviaxo/RiskShard/issues/new?template=request_a_shard.md)**
form — country, industry, size, threat, and what you would use it for. It applies the
`requested-shard` label itself; you do not need to set one, and an outside contributor has
no permission to.

**Building the cell yourself does not get around the freeze** — ADR-0016 part 2 declines
a new cell however complete the pack. What is open, and wanted, is strengthening a number
in one of the 11 existing shards: see [CONTRIBUTING.md](../CONTRIBUTING.md) and the
end-to-end [GOLDEN_CONTRIBUTOR_EXAMPLE.md](GOLDEN_CONTRIBUTOR_EXAMPLE.md).

## The list

| Scenario (country · sector · threat) | Requested by | Status | Link |
|---|---|---|---|
| JP · manufacturing · ransomware | maintainer | in progress — 4/6, scoped out of v0.1.0 | — |

*(Seeded with the one known open scaffold. New rows land here as requests come in.
**No outside request has arrived yet** — the only row is the maintainer's own, which is
why this page is a demand signal reading zero rather than a queue.)*
