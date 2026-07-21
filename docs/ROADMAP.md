# ROADMAP — emergent risk scenarios

*Proposed 2026-07-20. This is a strategic direction doc (see
[`PUBLISHABLE_REQUIREMENTS.md`](PUBLISHABLE_REQUIREMENTS.md) → Change Control). It records
intent and sequencing; each item becomes a scoped objective in
[`NEXT_STEPS.md`](NEXT_STEPS.md) when picked up.*

## Thesis

The library now covers the **commoditized** cyber threats (BEC, data breach, ransomware,
insider misuse, third-party outage). Every risk tool models those. The differentiation for
an evidence-governed, AI-native risk library is to quantify what point-tools structurally
**cannot**: **AI-as-liability, correlated/systemic loss, and governance/regulatory loss.**

Emergent threats have thinner data — but RiskShard's maturity discipline is *built* for that.
An honest `governed_starter` emergent scenario, with anchors and loud caveats, beats a
competitor that either fakes precision or stays silent. Emergent scenarios ship
governed-starter by design and graduate as evidence matures.

## The three families

### Family A — AI as liability (not just AI as attacker)
The obvious framing is "attackers use AI." The differentiating framing is "**your own AI
creates loss**" — and several forms already have documented, quantifiable anchors.

| Scenario | Why it matters | Impact anchors (documented) | Data gap | Model fit |
|---|---|---|---|---|
| **AI / deepfake-enabled fraud** | Extends BEC into the AI era | Arup Hong Kong ~USD 25.6M (2024); Singapore ~USD 4.9M deepfake case; Deloitte GenAI-fraud forecasts | frequency (incidence surveys, thin) | freq + single-event impact tail — **fits current schema** |
| **AI output / decision liability** | New litigable loss form as orgs deploy customer-facing AI | *Air Canada* chatbot liability ruling (2024); NYT v. OpenAI-class training-data suits | frequency of adverse rulings | freq + litigation-cost impact |
| **Agentic-AI compromise** | AI agents with tool access → unauthorized actions (payments, exfiltration) | early/thin — 2026-27 frontier | both freq and impact thin | freq + impact; honest scaffold |
| **EU AI Act penalty exposure** | Legislatively-defined penalty up to €35M / 7% turnover (higher than GDPR); AI-native; owned by nobody | AI Act penalty tiers (statutory); early enforcement | frequency = enforcement probability | freq + statutory-cap impact — **fits current schema** |

### Family B — correlated / systemic loss (what makes cyber actuarially different)
Cyber's defining property is **correlation**: one event hits thousands of orgs at once.
Point-tools model single-org loss and miss it. RiskShard already does portfolio aggregation,
so it can model cyber-**catastrophe** honestly.

| Scenario | Why it matters | Impact anchors | Data gap | Model fit |
|---|---|---|---|---|
| **Correlated single-vendor outage** | CrowdStrike Jul-2024 = the board example of concentration risk | Parametrix ~USD 5.4B Fortune-500 direct-loss estimate; insured-loss figures | per-org allocation of systemic loss | low freq × extreme impact — **fits current schema (tail scenario)** |
| **Identity-provider cascade** | One IdP breach → downstream access everywhere | Okta 2023 breach (documented) | per-org impact | freq + cascade impact |
| **Cyber insurability / risk-transfer failure** | The *meta-risk*: coverage evaporates (war exclusions, systemic-event exclusions) | Merck/NotPetya ~USD 1.4B war-exclusion litigation | frequency of denial | scenario over the mitigation itself |
| **Real-time-payment irreversibility** | Instant rails (FedNow) remove the clawback tail — re-shapes BEC impact | SG case: USD 6.66M sent, >USD 5M recovered → recovery → 0 on instant rails | — | **re-shapes existing BEC impact curve, not a new threat** |

### Family C — governance / regulatory loss (the GRC-native gap)
Cyber tools stop at the technical breach. A GRC product should own the downstream
governance loss the breach triggers.

| Scenario | Why it matters | Impact anchors | Data gap | Model fit |
|---|---|---|---|---|
| **Regulatory enforcement** (DORA / SEC cyber / NIS2 / privacy) | Almost no cyber tool models regulatory loss as its own scenario | GDPR enforcement tracker; SEC actions (SolarWinds); DORA in force Jan-2025 | frequency = enforcement probability | freq + fine-distribution impact — **fits current schema** |
| **Securities / disclosure liability** | Post-SEC 4-day rule: mishandled disclosure → stock drop + shareholder suits | SolarWinds SEC action | frequency | freq + litigation/market-cap impact |
| **Officer personal liability (D&O for cyber)** | CISOs/directors personally exposed | Uber CISO (Sullivan) criminal conviction | frequency | governance-risk scenario |

## The bigger strategic question (needs an ADR before it drives a build)

The sharpest differentiation may be modeling **loss *chains*, not threats**: one initiating
event → regulatory penalty → disclosure liability → insurability gap → personal liability.
That chain is what a board loses sleep over, and a threat-label library cannot express it.

RiskShard's engine already does distributions and aggregation, so this is a **schema/scenario
evolution, not a rewrite** — but it *is* a schema decision and must go through Change Control
(an ADR) before any loss-chain scenario is built. Until then, build only schema-compatible
scenarios (single threat → frequency × impact distributions).

## Proposed sequencing

**Schema-compatible now (no ADR needed):**
1. **AI / deepfake-enabled fraud** — sharpest differentiator, documented impact tails, extends BEC. *First build.*
2. **Correlated single-vendor outage** — extends third-party outage into a cyber-cat tail; strong data.
3. **EU AI Act penalty exposure** — AI-native, statutory impact, owned by nobody.
4. **Regulatory enforcement** — GRC-native; strong fines-based impact data.

**Needs the loss-chain ADR first:** insurability failure, securities/disclosure liability,
officer personal liability, and any multi-hop chain.

**Roadmap-far (data too thin today):** agentic-AI compromise, post-quantum "harvest now,
decrypt later." Track; do not build until loss data exists.

## Proposed taxonomy additions

New `taxonomies/threats.yaml` ids to introduce as their scenarios are built (do not add an id
without at least one evidence record): `ai_enabled_fraud`, `systemic_vendor_outage`,
`regulatory_enforcement`, `ai_governance_penalty`. (`cloud_compromise` already exists as an
unused placeholder.)
