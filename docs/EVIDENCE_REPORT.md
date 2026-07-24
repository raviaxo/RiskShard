# RiskShard Evidence Report

Every model parameter in every shard, with the source it traces to and the caveat that limits it. Generated from the governed evidence — nothing here is hand-written. Dispute any row: `riskshard_modules.py provenance <shard> --dispute <param>`.

**Portfolio:** 11 shards · 66 of 66 parameters source-backed · 0 bridged/estimated · 0 missing.

## au_finance_bec_midmarket
_Australia Finance Business Email Compromise Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.00010514176186819692 annual_probability | source_backed | ACCC Targeting Scams Report 2025 and ABS Counts of Australian Businesses 2024-25 (2026-03-30) | Scamwatch loss reports are not complete BEC events, not financial-services-specific, and the denominator is all Australian businesses rather than mid-market financial-services firms. |
| `frequency.likely` | 0.21 annual_probability | source_backed | Characteristics of Australian Business, 2024-25 (2026-06-25) | All-industry, all-size, all-cyber measure, not BEC-specific and not mid-market-financial-services-specific; it counts businesses experiencing any cyber security incident, not confirmed BEC loss events, so it overstates BEC-only frequency. Revise when BEC-specific AU mid-market evidence is reviewed. |
| `frequency.max` | 0.81 annual_probability | source_backed | MYOB mid-sized business cyber attack survey 2024 (2024-06-01) | Commercial vendor survey (MYOB/Dynata), lower trust than official statistics; measures all cyber attacks, not BEC-specific, and counts businesses experiencing an attack rather than confirmed BEC loss events; mid-sized defined as 20-500 FTE with revenue over AUD 5M. Revise when official AU finance mid-market BEC frequency is available. |
| `impact.min` | 33101.05 currency | source_backed | ACCC Targeting Scams Report 2025 (2026-03-30) | Scam-wide small-business average from Scamwatch reports, not BEC-only, financial-services-specific, mid-market-specific, or a full severity distribution. |
| `impact.likely` | 123005.43 currency | source_backed | FBI IC3 2025 Annual Report (2026-04-16) | US IC3 complaint population; self-reported and complaint-driven; not Australia-specific, financial-services-specific, mid-market-specific, or a full loss distribution. |
| `impact.max` | 2000000 currency | source_backed | ACCC Targeting Scams Report 2025 (2026-03-30) | Aggregate small-business Scamwatch losses; not financial-services-specific, mid-market-specific, or a direct tail quantile. |

## au_finance_data_breach_midmarket
_Australia Finance Data Breach Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.0008 annual_probability | source_backed | OAIC NDB Report July-Dec 2024 and ABS Counts of Australian Businesses 2024-25 (2025-05-13) | Covers eligible Australian NDB notifications only; all-size sector denominator is not mid-market-specific; multiple notifications by one entity and unreported/non-reportable breaches can distort organization-level probability. Confidence is medium for a reported-notification floor, not for a likely breach rate. |
| `frequency.likely` | 0.65 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | UK official survey; covers identified cyber breaches or attacks, not privacy-only data breaches; not Australia-specific, not financial-services-specific, and may include high-volume low-impact events. |
| `frequency.max` | 0.69 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | UK official survey; covers identified cyber breaches or attacks, not privacy-only data breaches; large-business prevalence can overstate mid-market likelihood; not Australia-specific or financial-services-specific. |
| `impact.min` | 97200 currency | source_backed | Business Queensland Keeping your business cyber secure (2025-10-23) | Secondary government guidance page that links to ASD as the primary source; cybercrime-wide rather than data-breach-specific, not financial-services-specific, and not a loss distribution quantile. |
| `impact.likely` | 4400000 currency | source_backed | IBM Cost of a Data Breach Report 2025 (2025-07-30) | Global average across studied breached organizations; not Australia-specific, financial-services-specific, or size-band-specific. |
| `impact.max` | 50000000 currency | source_backed | Privacy Act 1988 (2026-06-04) | Statutory maximum penalty cap, not a total event-loss estimate, not expected loss, not financial-services-specific, and actual penalties depend on regulator and court facts. |

## au_finance_ransomware_midmarket
_Australia Finance Ransomware Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.1 annual_probability | source_backed | Cyentia IRIS Ransomware (2025-04-21) | Global cross-sector estimate; not Australia-specific and not financial-services-specific. |
| `frequency.likely` | 0.65 annual_probability | source_backed | Sophos State of Ransomware in Financial Services 2024 (2024-06-24) | Global financial-services survey, not Australia-specific; survey population may not equal the target organization's peer group. |
| `frequency.max` | 0.65 annual_probability | source_backed | Sophos State of Ransomware in Financial Services 2024 (2024-06-24) | Global financial-services survey, not Australia-specific; using the same 65% statistic for likely and max means the frequency range is intentionally conservative and awaits better tail-frequency evidence. |
| `impact.min` | 97200 currency | source_backed | Business Queensland Keeping your business cyber secure (2025-10-23) | Secondary government guidance page that links to ASD as the primary source; cybercrime-wide rather than ransomware-specific, not financial-services-specific, and not a loss distribution quantile. |
| `impact.likely` | 2580000 currency | source_backed | Sophos State of Ransomware in Financial Services 2024 (2024-06-24) | Global financial-services value, not Australia-specific; the public article does not provide size-band segmentation. |
| `impact.max` | 52000000 currency | source_backed | Cyentia Information Risk Insights Study 2022 (2022-01-01) | Global cyber-event loss benchmark, not Australia-specific, ransomware-only, financial-services-specific, or a formal ransomware claim-severity percentile. Use as an automated benchmark-review stress bridge only with human caveat review. |

## ca_finance_data_breach_midmarket
_Canada Finance Data Breach Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.2436 annual_probability | source_backed | OPC 2025-2026 Annual Report to Parliament (2026-06-04) | Combines a cross-sector organization survey fact with a conditional PIPEDA reported-breach harm share; not financial-services-specific, mid-market-specific, or a denominator-backed sector incident rate. |
| `frequency.likely` | 0.42 annual_probability | source_backed | OPC 2025-2026 Annual Report to Parliament (2026-06-04) | Cross-sector Canadian organization survey fact cited by OPC/CIRA; not limited to financial services, mid-market companies, material events, or regulator-reportable breaches. |
| `frequency.max` | 0.42 annual_probability | source_backed | OPC 2025-2026 Annual Report to Parliament (2026-06-04) | Cross-sector Canadian organization survey fact cited by OPC/CIRA; not limited to financial services, mid-market companies, material events, or regulator-reportable breaches. |
| `impact.min` | 266000 currency | source_backed | Cyentia Information Risk Insights Study 2022 (2022-01-01) | Global cyber-event benchmark, not Canada-specific, data-breach-only, financial-services-specific, or a true minimum loss quantile. Accept only as a benchmark-review bridge with this caveat. |
| `impact.likely` | 6980000 currency | source_backed | IBM Canada newsroom release, Cost of a Data Breach Report 2025 (2025-07-30) | Primary IBM Canada release, but an all-sector national average across studied breached organizations, not mid-market-specific or financial-services-specific; IBM's sample skews toward larger organizations, so this is an upper-leaning mid-market likely anchor. |
| `impact.max` | 32000000 currency | source_backed | Cyentia Information Risk Insights Study 2025 (2025-06-10) | Global security-incident benchmark, not Canada-specific, data-breach-only, financial-services-specific, or a formal percentile for this scenario. Accept only as a benchmark-review stress bridge with this caveat. |

## de_industrial_ransomware_midmarket
_Germany Industrial Ransomware Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.1 annual_probability | source_backed | Cyentia IRIS Ransomware (2025-04-21) | Global cross-sector estimate; not Germany-specific, manufacturing-specific, or size-band-specific. |
| `frequency.likely` | 0.34 annual_probability | source_backed | Bitkom Wirtschaftsschutz 2025 (2025-12-01) | Cross-industry Germany company survey; not manufacturing-specific, not limited to mid-market organizations, and reflects damage-causing ransomware rather than all attack attempts. |
| `frequency.max` | 0.59 annual_probability | source_backed | Bitkom Wirtschaftsschutz 2025 (2025-12-01) | Derived from survey basis counts rather than a standalone plotted rate; cross-industry, survey-based, and broader than damage-causing ransomware. |
| `impact.min` | 10000 currency | source_backed | Bitkom Wirtschaftsschutz 2025 (2025-12-01) | Payment-only lower-band anchor, not total event loss, recovery cost, downtime, or a Germany industrial claims distribution. |
| `impact.likely` | 1300000 currency | source_backed | Sophos State of Ransomware in Manufacturing and Production 2025 (2025-12-04) | Global manufacturing survey of organizations hit by ransomware; excludes ransoms paid, is not Germany-specific, and is not a full total-loss distribution. |
| `impact.max` | 5000000 currency | source_backed | Sophos State of Ransomware in Manufacturing and Production 2025 (2025-12-04) | Threshold for extreme ransom demands and payouts, not total event loss, not Germany-specific, and not a formal percentile or upper bound. |

## fr_finance_data_breach_midmarket
_France Finance Data Breach Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.0198 annual_probability | source_backed | Eurostat ISOC_CISCE_IC - ICT security incidents by size class (France) (2025-10-08) | Eurostat survey population excludes the financial sector (nace_r2 = C10-S951_X_K), so this is a non-financial-sector proxy; self-reported disclosure incidents are narrower than "any cyberattack"; small-enterprise rate used as a floor. |
| `frequency.likely` | 0.0383 annual_probability | source_backed | Eurostat ISOC_CISCE_IC - ICT security incidents by size class (France) (2025-10-08) | Eurostat survey population excludes the financial sector, which is typically more targeted, so this likely understates; self-reported disclosure incidents are narrower than "any cyberattack." |
| `frequency.max` | 0.073 annual_probability | source_backed | Eurostat ISOC_CISCE_IC - ICT security incidents by size class (France) (2025-10-08) | Eurostat survey population excludes the financial sector, which is typically more targeted, so this likely understates; large-enterprise rate used as an upper bound for a mid-market shard. |
| `impact.min` | 58600 currency | source_backed | Asteres - Le cout des cyberattaques reussies en France (2022) (2023-06-16) | Economy-wide France average across all organization sizes and all cyberattack types, not data-breach-specific, financial-services-specific, or a true minimum quantile. Used only as a conservative lower-bound anchor. |
| `impact.likely` | 3590000 currency | source_backed | Rapport IBM 2025 : coût d'une violation de données en France (2025-07-30) | All-sector France national average, not mid-market- or financial-services-specific; based on 34 French organizations and enterprise-weighted, so treat as an upper-leaning mid-market likely anchor. The France financial-services sub-figure (EUR 4.65M) rests on a small sample and is recorded as sector context, not the selected anchor. |
| `impact.max` | 20000000 currency | source_backed | GDPR Article 83(5) maximum administrative fine (via CNIL) (2018-05-25) | Statutory maximum penalty cap, not a total event-loss estimate, expected loss, or claims severity; actual fines depend on regulator and case facts. |

## gb_finance_data_breach_midmarket
_United Kingdom Finance Data Breach Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.43 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | Covers identified breaches or attacks, not privacy-only data breaches; hidden or unidentified events may be absent; all-business figure is not financial-services-specific. |
| `frequency.likely` | 0.65 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | Covers identified breaches or attacks, not privacy-only data breaches; not financial-services-specific and may include high-volume low-impact events. |
| `frequency.max` | 0.69 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | Covers identified breaches or attacks, not privacy-only data breaches; larger organization prevalence may overstate mid-market frequency. |
| `impact.min` | 10000 currency | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | Perceived cost of the most disruptive breach or attack; broader than privacy breach cost; sample and cost definition differ from enterprise breach-cost studies. Confidence is medium only for use as a conservative UK mid-market material-cost floor. |
| `impact.likely` | 5740000 currency | source_backed | IBM UK Cost of a Data Breach 2025 release (2025-07-30) | Surveyed/studied breach population; sponsor methodology; not mid-market-specific, not a full distribution, and not a regulator-reported loss table. |
| `impact.max` | 11164400 currency | source_backed | FCA fines Equifax Ltd over cyber security breach (2023-10-13) | Regulatory penalty only; not total event loss, insurance claim severity, or a full tail distribution; the incident was a large credit-reference data breach, not a mid-market-specific loss sample. Confidence is medium only for use as a source-backed UK regulatory stress anchor. |

## jp_manufacturing_ransomware_midmarket
_Japan Manufacturing Ransomware Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.1 annual_probability | source_backed | Cyentia IRIS Ransomware (2025-04-21) | Global cross-sector estimate; not Japan-specific, manufacturing-specific, or size-band-specific. |
| `frequency.likely` | 0.56 annual_probability | source_backed | Sophos State of Ransomware in Manufacturing and Production 2024 (2024-05-28) | Global survey of organizations with 100-5,000 employees (17 countries; not confirmed to include Japan), not Japan-specific or size-band-specific. Reports ATTACK prevalence ("hit by ransomware"), which OVERSTATES loss-event frequency: in the 2025 report only ~40% of manufacturing attacks resulted in encryption. Survey respondents (orgs with IT/security leaders) may overstate population prevalence, and the 55/56/65% series is rising, so a point estimate hides the trend. Read the frequency as attack-incidence on the same basis as the impact side.  |
| `frequency.max` | 0.65 annual_probability | source_backed | Sophos State of Ransomware in Manufacturing and Production 2024 (2024-05-28) | Highest observed year of a rising 55/56/65% (2022/2023/2024) series, so it is a recent peak rather than a formal tail percentile. Global survey of organizations with 100-5,000 employees (not Japan-specific). Reports ATTACK prevalence, which OVERSTATES loss-event frequency (only ~40% of 2025 manufacturing attacks encrypted). Read as attack-incidence on the same basis as the impact side.  |
| `impact.min` | 1000000 currency | source_backed | National Police Agency of Japan 2025 Cyber Threat Situation Statistics Data (2026-03-09) | Investigation/restoration cost band only; excludes broader business interruption, ransom, legal, customer, and strategic impacts. |
| `impact.likely` | 1300000 currency | source_backed | Sophos State of Ransomware in Manufacturing and Production 2025 (2025-12-04) | Global survey of organizations hit by ransomware; not Japan-specific and excludes ransom payments. |
| `impact.max` | 5000000 currency | source_backed | Sophos State of Ransomware in Manufacturing and Production 2025 (2025-12-04) | Threshold for extreme ransom demands and payouts; not Japan-specific, not total event loss, and not a formal percentile. |

## sg_finance_bec_midmarket
_Singapore Finance Business Email Compromise Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.004 annual_probability | source_backed | FBI IC3 2025 Annual Report and U.S. Census SUSB 2022 (2026-04-16) | GLOBAL BRIDGE, NOT SINGAPORE-SPECIFIC. Both numerator and denominator are United States figures (IC3 complaints, US Census firms); used only as a conservative global reported-complaint floor until a Singapore denominator-derived BEC frequency (e.g. SPF business-email-impersonation cases over SingStat enterprise counts) is reviewed. |
| `frequency.likely` | 0.63 annual_probability | source_backed | 2025 AFP Payments Fraud and Control Survey Report (2025-08-26) | GLOBAL BRIDGE, NOT SINGAPORE-SPECIFIC. US survey; measures organizations experiencing attempted or actual BEC, not confirmed loss events; respondents skew corporate-treasury and larger organizations. Revise when a Singapore organization-level BEC prevalence is reviewed. |
| `frequency.max` | 0.74 annual_probability | source_backed | 2026 AFP Payments Fraud and Control Survey Report (2026-04-14) | GLOBAL BRIDGE, NOT SINGAPORE-SPECIFIC. US survey, attempts/affected not confirmed loss events, large-organization skew. Revise when a Singapore stress-frequency is reviewed. |
| `impact.min` | 50000 currency | source_backed | Verizon 2026 Data Breach Investigations Report (2026-05-20) | GLOBAL BRIDGE, NOT SINGAPORE-SPECIFIC. Median of FBI IC3 complaint-reported (US) BEC losses; complaint-driven and self-reported; not a Singapore or mid-market figure. Revise when a Singapore BEC loss floor is reviewed. |
| `impact.likely` | 123005.43 currency | source_backed | FBI IC3 2025 Annual Report (2026-04-16) | US IC3 complaint population; not Singapore-specific, financial-services-specific, mid-market-specific, or a full loss distribution. |
| `impact.max` | 6660000 currency | source_backed | SPF Business Email Compromise scam interception case 2024 (2024-10-08) | One documented extreme Singapore BEC case (an investment banking firm), not a mid-market average or a loss percentile; over USD 5M was intercepted, but recovery is not guaranteed so the gross figure is modeled. Revise when a Singapore BEC loss distribution with tail quantiles is reviewed. |

## us_finance_bec_midmarket
_United States Finance Business Email Compromise Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.004 annual_probability | source_backed | FBI IC3 2025 Annual Report and U.S. Census SUSB 2022 (2026-04-16) | IC3 counts only complaints reported to the FBI and substantially undercounts true BEC incidence; numerator and denominator are both all-sector/all-industry, so this is an economy-wide reported floor, not financial-services-specific or mid-market-specific; it is a lower-bound floor, not a central likelihood. Confidence is medium for a reported-complaint floor, not for a likely BEC rate. |
| `frequency.likely` | 0.63 annual_probability | source_backed | 2025 AFP Payments Fraud and Control Survey Report (2025-08-26) | Survey measures organizations experiencing attempted or actual BEC, not confirmed financial-loss events; AFP respondents skew toward corporate treasury and larger organizations (AFP reports 66% of BEC attempts target organizations with at least USD 1B revenue), so this overall prevalence likely overstates a mid-market financial-services rate; not financial-services-specific. Revise when mid-market-specific BEC event-frequency evidence is reviewed. |
| `frequency.max` | 0.74 annual_probability | source_backed | 2026 AFP Payments Fraud and Control Survey Report (2026-04-14) | Survey measures organizations experiencing attempted or actual BEC, not confirmed financial-loss events; AFP respondents skew toward corporate treasury and larger organizations, so this overall prevalence likely overstates a mid-market financial-services rate; it is drawn from the subsequent (2026) AFP edition rather than the same edition as the likely bridge; not financial-services-specific. Revise when mid-market-specific BEC event-frequency evidence is reviewed. |
| `impact.min` | 50000 currency | source_backed | Verizon 2026 Data Breach Investigations Report (2026-05-20) | Median of FBI IC3 complaint-reported BEC losses as presented by Verizon DBIR; complaint-driven and self-reported, not financial-services-specific or mid-market-specific, and not a formal minimum quantile for this scenario. |
| `impact.likely` | 123005.43 currency | source_backed | FBI IC3 2025 Annual Report (2026-04-16) | US IC3 complaint population; self-reported and complaint-driven; not financial-services-specific, mid-market-specific, or a full loss distribution. |
| `impact.max` | 6400000 currency | source_backed | Coalition funds transfer fraud largest clawback case (2023-06-08) | One documented extreme funds-transfer-fraud case from a cyber insurer's book, not a modeled loss percentile or a financial-services mid-market average; 85% was recovered via clawback in this instance, but recovery is not guaranteed, so the gross figure is modeled; BEC/FTF-specific but drawn from a single case. Revise when a US mid-market BEC loss distribution with tail quantiles is reviewed. |

## us_finance_data_breach_midmarket
_United States Finance Data Breach Midmarket_

| Parameter | Value | Status | Source | Caveat |
| --- | --- | --- | --- | --- |
| `frequency.min` | 0.43 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | UK official survey used as a bridge; not US-specific and not financial-services-specific; covers identified breaches or attacks, broader than privacy-only data breach. |
| `frequency.likely` | 0.65 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | UK official survey used as a bridge; not US-specific and not financial-services-specific; may include high-volume low-impact events. |
| `frequency.max` | 0.69 annual_probability | source_backed | Cyber Security Breaches Survey 2025/2026 (2026-04-30) | UK official survey used as a bridge; not US-specific and not financial-services-specific; large-business prevalence can overstate mid-market likelihood. |
| `impact.min` | 152000 currency | source_backed | NetDiligence Cyber Claims Study 2025 (Fifteenth Annual) (2025-09-23) | Insured-claim crisis-services subset; not full total loss; SME band is broad (under USD 2B revenue) and not isolated to financial services. |
| `impact.likely` | 264000 currency | source_backed | NetDiligence Cyber Claims Study 2025 (Fifteenth Annual) (2025-09-23) | Insured-claim sample; SME band is broad and not isolated to financial services; excludes uninsured or unreported losses. |
| `impact.max` | 5560000 currency | source_backed | Cost of a Data Breach Report 2025 (2025-07-30) | Enterprise-weighted studied breach population; not mid-market-specific and not a full tail distribution; used as a scale stress anchor, not an expected mid-market loss. |
