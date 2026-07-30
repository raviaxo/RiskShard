# Impact-source scout — Canada and Australia (2026-07-30)

*Research note. Written so the next session does not re-run this scout. No evidence or
model change resulted; the decisions are recorded below.*

## Why these two

They held the weakest impact anchors in the portfolio: Canada's `impact.min` and
`impact.max` both rest on Cyentia IRIS (a generic cross-cyber, global loss study), and
Australia's `impact.min` cited a secondary government guidance page. Both countries have
official statistical agencies that publish cyber cost data, so both looked upgradeable.

## Australia — already handled correctly; nothing to change

**Verified at the primary source** (ASD *Annual Cyber Threat Report 2024–25*, read at
cyber.gov.au 2026-07-30):

> Average self-reported cost of cybercrime per report for businesses, up 50% overall
> ($80,850) — small business: $56,600 (up 14%), **medium business: $97,200 (up 55%)**,
> large business: $202,700 (up 219%)

That confirms the `97200` already used by `au_finance_data_breach_midmarket` and
`au_finance_ransomware_midmarket` as `impact.min`.

The apparent upgrade — swap the Business Queensland citation for the primary ASD report —
**was already considered and consciously rejected by an earlier session**, and the reason is
recorded in the manifest entry itself:

> "Treat it as a secondary bridge source until the primary ASD artifact is gatherable in
> this runtime."

That remains true: `cyber.gov.au` is not fetchable from this runtime (curl returns
`http=000`; the PDF and the HTML page both fail). The repo's rule is that a registered
source has a real fetched artifact, so a secondary page that *is* gatherable and that
quotes the primary correctly is the honest choice. **Left alone.**

The one thing this scout adds: the ASD figures are now **verified against the primary
source**, not merely assumed to be quoted correctly. That is recorded here rather than in
`sources/manifest.json` deliberately — the manifest is inside the data pack, so editing it
for a documentation-only note would change the pack fingerprint and produce a spurious
strength-ledger signal for a change that improves nothing.

## Canada — decision: leave as-is, known-weak

**StatCan's Canadian Survey of Cyber Security and Cybercrime** publishes (reference year
2023, *The Daily*, 2024-10-21):

- total recovery spending **$1.2 billion**, of which **~$300 million** for medium-sized
  businesses (50–249 employees); large ~$500M, small ~$300M
- prevention and detection spending $11.0 billion (medium: $3.6 billion)
- **16%** of Canadian businesses impacted by an incident
- **no per-business average cost**

Two problems make this a worse anchor than it appears:

1. **It requires a derivation.** A per-business figure means dividing ~$300M by a count of
   affected medium businesses — needing both a Canadian medium-business population and a
   medium-specific incident rate. That is the IC3÷Census pattern, but with two assumed
   inputs rather than one.
2. **"Recovery spending" is narrower than loss.** It excludes business interruption, lost
   revenue, ransom payments and legal costs. Swapping it in for a Cyentia loss figure would
   *look* like an upgrade to an official national source while silently narrowing what the
   parameter measures.

**Decision (owner, 2026-07-30): leave Cyentia in place and treat Canada as a known-weak
shard until better data exists.** A narrower measure dressed as an upgrade is exactly what
[ADR-0003](../adr/0003-shared-impact-bridges.md) exists to make visible.

## Correction to ADR-0003

ADR-0003's recommendation previously argued for sequencing the bridge-marking work *after*
the CA/AU upgrades, on the grounds that they "would retire three of the six bridges". That
is wrong on both counts and has been fixed:

- Canada is not being upgraded (decision above), so its two Cyentia bridges stay.
- Australia's ASD figure is `impact.min`; the Cyentia bridge in `au_finance_ransomware` is
  `impact.max`. Upgrading the citation would not have touched it.

So no bridge is retired by this scout, and there is no longer a sequencing reason to delay
the ADR-0003 work.

## What is still worth scouting for impact

- **NetDiligence by revenue band** — already registered, used only for the US, and it
  publishes severity by revenue band across fifteen editions. The highest-value unmined
  source in the manifest.
- **NAIC Cyber Insurance Supplement** — regulator-published premiums, claim counts and paid
  losses.
- **Singapore** — the whole impact side is borrowed US data (IC3, DBIR) and no local source
  has been found. The most bridged shard in the portfolio.
