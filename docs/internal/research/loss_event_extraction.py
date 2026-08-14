#!/usr/bin/env python3
"""Emit loss_events/sec_filings_2023_2026.yaml from a hand-verified table.

ADR-0012 requires verification-assisted extraction and forbids automatic. The table
below IS the verification: every row was read from the filing sentence quoted in
`cited_line`, its amount typed by hand, and its units resolved against the statement
header where the sentence alone was ambiguous. The census
(`../edgar_corpus_census.md`) produced the candidates; this produced the records.

**Two candidates the census accepted are rejected here**, because a registry record is
held to a higher standard than a census candidate:

- **SolarWinds** — the `$15 million` is *cybersecurity insurance coverage we maintain*,
  a policy limit, not a loss and not a recovery. Same error as SIFCO, which the census
  did catch. The census recorded SolarWinds as `$15M insurance proceeds`; that reading
  came from a looser sentence and does not survive the filing.
- **Coinbase** — `$345,210` thousand is the *"Platform-related incidents"* expense
  line, a category spanning more than one event. It is not attributable to a single
  incident, and this registry records events.

So the census's 38 becomes **36**. That is the verification pass doing its job, and it
is recorded rather than quietly reconciled.

Units resolved, per the census hazard (a face-value read of a table figure is wrong by
1000x): AvidXchange, Bassett, Hanesbrands, Bancorp 34 and Data I/O all state amounts in
thousands or in bare dollars. Where a filing gave both forms — AvidXchange's `$302` and
`$0.3 million`, Hanesbrands' `$15,509` and `$15 million` — the explicit form is used and
the ambiguous one is noted.

Not product code: not wired into the CLI, not covered by the test suite. Kept so the
records can be regenerated and checked.

Usage:  python loss_event_extraction.py > ../../../loss_events/sec_filings_2023_2026.yaml
"""
import sys

EXTRACTED = "2026-08-14"
VERIFIER = "raviaxo"

# Corpus-level limits every record inherits. ADR-0005's three structural biases, which
# ADR-0012 carried forward unchanged.
CORPUS_LIMITS = (
    "One documented event, not a distribution. The corpus is biased toward listed "
    "entities, censored at each filer's own materiality threshold, and figures are "
    "often provisional and settle in later periods. Usable as a tail or defensibility "
    "anchor with those caveats attached; never to be aggregated into an average, and it "
    "carries no exceedance probability."
)

# (id, name, cik, country, industry, listed, threat, date, precision, description,
#  [(type, value, currency, basis, period, status, units_from, cited_line)],
#  filing_type, url, filing_date, extra_limitation)
EVENTS = [
    ("sec_23andme_2023_credential_stuffing", "23andMe Holding Co.", "0001804591", "US",
     "biotechnology", True, "data_breach", "2023-10", "month",
     "Credential-stuffing incident affecting customer profile data; settled by class action.",
     [("legal_settlement", 30_000_000, "USD", "gross", "settlement term sheet 2024-07-29", "provisional", None,
       "The parties executed a confidential settlement term sheet on July 29, 2024, which contemplated an aggregate cash payment by the Company of $ 30.0 million to settle all claims brought on behalf of all persons in the United States whose personal information was impacted"),
      ("direct_cost", 19_800_000, "USD", "net_of_insurance", "nine months ended 2024-12-31", "provisional", None,
       "During the nine months ended December 31, 2024, the Company recognized $ 19.8 million in net expenses related to the Cyber Incident primarily consisting of $ 42.0 million in legal fees incurred and estimated loss contingencies, partially offset by probable insurance rec")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1804591/000180459125000012/me-20241231.htm", "2025-02-06",
     "The settlement and the expense line overlap; they are separate typed amounts and must not be summed."),

    ("sec_americold_2023_cyber_incident", "AMERICOLD REALTY TRUST", "0001455863", "US",
     "logistics", True, "unspecified_cyber_incident", "2023-04", "month",
     "Cyber incident requiring remediation and response effort across warehouse operations.",
     [("direct_cost", 24_400_000, "USD", "gross", "nine months ended 2023-09-30", "provisional", None,
       "Incremental charges recorded in conjunction with remediation and response efforts associated with the Cyber Incident were $ 5.4 million and $ 24.4 million during the three and nine months ended September 30, 2023, respectively")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1455863/000162828023036379/art-20230930.htm", "2023-11-02", None),

    ("sec_ardent_health_2023_ransomware", "Ardent Health Partners, Inc.", "0001756655", "US",
     "healthcare", True, "ransomware", "2023-11", "month",
     "Ransomware incident affecting hospital operations over the 2023 Thanksgiving period.",
     [("total_event_impact", 74_000_000, "USD", "gross", "year ended 2023-12-31", "final", None,
       "We estimate the Cybersecurity Incident had an adverse pre-tax impact of approximately $74 million during the year ended December 31, 2023."),
      ("insurance_recovery", 2_900_000, "USD", "gross", "three months ended 2024-09-30", "final", None,
       "The increase in other non-operating gains was primarily due to the recognition of insurance recovery proceeds of $2.9 million during the three months ended September 30, 2024 related to the Cybersecurity Incident.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1756655/000175665524000017/ardt-20240930.htm", "2024-11-07", None),

    ("sec_avidxchange_2023_cyber_incident", "AvidXchange Holdings, Inc.", "0001858257", "US",
     "financial_services", True, "unspecified_cyber_incident", "2023", "year",
     "Cyber incident at an accounts-payable automation provider; response costs across two fiscal years.",
     [("direct_cost", 5_400_000, "USD", "gross", "year ended 2023-12-31", "final", None,
       "During the years ended December 31, 2024 and 2023, we incurred $0.3 million and $5.4 million, respectively, in response costs related to the incident, including professional services and legal fees, and recorded insurance recoveries of $2.1 million and $1.7 million, res"),
      ("insurance_recovery", 1_700_000, "USD", "gross", "year ended 2023-12-31", "final", None,
       "recorded insurance recoveries of $2.1 million and $1.7 million, respectively")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1858257/000095017025029974/avdx-20241231.htm", "2025-02-28",
     "A separate sentence in the same filing states the 2024 figure as '$ 302', denominated in thousands; the million-form is used here to avoid a 1000x misread."),

    ("sec_bancorp34_2023_cyber_incidents", "Bancorp 34, Inc.", "0001668340", "US",
     "financial_services", True, "unspecified_cyber_incident", "2023", "year",
     "Cybersecurity incidents disclosed by a small bank holding company.",
     [("direct_cost", 25_000, "USD", "not_stated", "to date at 2024-03-08", "provisional", "figure stated in whole dollars in the filing text",
       "To date, we have incurred expenses of approximately $25,000 related to the cybersecurity incidents.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1668340/000155278124000084/e24045_bctf-10k.htm", "2024-03-08",
     "Among the smallest documented figures in the corpus; useful as evidence that disclosure reaches small issuers, not as a typical value."),

    ("sec_bassett_furniture_2024_cyber_incident", "BASSETT FURNITURE INDUSTRIES INC", "0000010329", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2024-07", "month",
     "Cybersecurity incident causing a production shutdown and work stoppage.",
     [("direct_cost", 98_000, "USD", "not_stated", "third quarter fiscal 2024", "provisional", "consolidated statements denominated in thousands",
       "During the third quarter of 2024, we also incurred legal and remediation costs related to the incident of approximately $98 which are included in selling, general and administrative expenses."),
      ("revenue_impact", 1_500_000, "USD", "not_stated", "fiscal 2024", "provisional", "consolidated statements denominated in thousands; filing states a $1,000-$2,000 range",
       "we estimate that between $1,000 and $2,000 of sales were lost due to the shutdown during the cybersecurity incident")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/10329/000143774924031014/bset20240831d_10q.htm", "2024-10-10",
     "The revenue-impact figure is the midpoint of a range the filing gives as $1,000-$2,000 thousand; the filing states a range, not a point."),

    ("sec_campbells_2023_cyber_incident", "CAMPBELL'S Co", "0000016732", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2023-Q4", "quarter",
     "Cybersecurity incident identified in the fourth quarter of fiscal 2023.",
     [("direct_cost", 3_000_000, "USD", "gross", "three months ended 2023-10-29", "final", None,
       "Insurance recoveries of $ 1 million and costs of $ 3 million related to a cybersecurity incident were included in the three-month periods ended October 27, 2024 and October 29, 2023, respectively."),
      ("insurance_recovery", 1_000_000, "USD", "gross", "three months ended 2024-10-27", "final", None,
       "In the first quarter of 2025, we recognized insurance recoveries in Administrative expenses of $1 million ($1 million after tax) related to a cybersecurity incident that was identified in the fourth quarter of 2023.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/16732/000001673224000201/cpb-20241027.htm", "2024-12-04", None),

    ("sec_conduent_2025_cyber_incident", "CONDUENT Inc", "0001677703", "US",
     "business_services", True, "unspecified_cyber_incident", "2025-01", "month",
     "January 2025 cyber incident at a business-process services provider.",
     [("direct_cost", 25_000_000, "USD", "gross", "three months ended 2025-03-31", "provisional", None,
       "Included in the 2025 period are $ 25 million of Direct response costs related to the January 2025 Cyber Incident and a $ 9 million insurance recovery related to the 2019 Texas Matter.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1677703/000167770325000076/cndt-20250331.htm", "2025-05-07",
     "The $9 million insurance recovery in the same sentence relates to a different, earlier matter and is deliberately not recorded against this event."),

    ("sec_data_io_2025_ransomware", "DATA I/O CORP", "0000351998", "US",
     "manufacturing", True, "ransomware", "2025-08", "month",
     "Ransomware incident shutting down most global operating systems and delaying shipments.",
     [("direct_cost", 388_000, "USD", "not_stated", "fiscal 2025", "provisional", "figure stated in whole dollars in the filing text",
       "In August 2025, the Company experienced a ransomware incident that resulted in the shutdown of most global operating systems, business disruptions including the inability to timely process certain shipments, and significant remediation costs of approximately $388,000")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/351998/000165495426003625/daio_10k.htm", "2026-04-16", None),

    ("sec_davita_2025_ransomware", "DAVITA INC.", "0000927066", "US",
     "healthcare", True, "ransomware", "2025-04", "month",
     "Ransomware incident affecting dialysis operations; remediation with third-party assistance.",
     [("direct_cost", 25_200_000, "USD", "gross", "nine months ended 2025-09-30", "provisional", None,
       "During the nine months ended September 30, 2025, we incurred patient care costs of approximately $1.0 million and general and administrative expenses of approximately $24.2 million related to the incident.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/927066/000092706625000165/dva-20250930.htm", "2025-10-29",
     "The recorded amount sums two components the filing states separately ($1.0M patient care + $24.2M G&A) for the same period; the filing does not print the total."),

    ("sec_f5_2025_cyber_incident", "F5, INC.", "0001048695", "US",
     "technology", True, "unspecified_cyber_incident", "2025-10", "month",
     "Cyber incident disclosed by a network security and application delivery vendor.",
     [("direct_cost", 26_500_000, "USD", "gross", "nine months ended 2026-06-30", "provisional", None,
       "The Company incurred $ 3.0 million and $ 26.5 million of costs in response to the Cyber Incident for the three and nine months ended June 30, 2026, respectively."),
      ("insurance_recovery", 5_300_000, "USD", "gross", "nine months ended 2026-06-30", "provisional", None,
       "The Company received $ 5.3 million in insurance recoveries for claims related to the Cyber Incident for the three and nine months ended June 30, 2026, respectively.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1048695/000104869526000067/ffiv-20260630.htm", "2026-08-06", None),

    ("sec_fidelity_national_financial_2023_cyber_incident", "Fidelity National Financial, Inc.", "0001331875", "US",
     "financial_services", True, "unspecified_cyber_incident", "2023-11", "month",
     "November 2023 cybersecurity incident at a title insurance and settlement services group.",
     [("period_delta", 10_000_000, "USD", "not_stated", "FY2024 vs FY2023", "final", None,
       "The decrease in the year ended December 31, 2024 as compared to 2023 is primarily attributable to a $10 million reduction in expenses related to the 2023 cybersecurity incident")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1331875/000133187525000013/fnf-20241231.htm", "2025-02-28",
     "This is a year-over-year REDUCTION in incident expense, not the cost of the event. It bounds nothing about the event total and must never be read as one."),

    ("sec_first_american_2023_cyber_incident", "First American Financial Corp", "0001472787", "US",
     "financial_services", True, "unspecified_cyber_incident", "2023-12", "month",
     "December 2023 cybersecurity incident causing a systems shutdown at a title insurer.",
     [("direct_cost", 11_000_000, "USD", "gross", "year ended 2023-12-31", "provisional", None,
       "Included in this 36 cent shortfall was $11 million of direct expenses related to the incident in our corporate segment including our $5 million insurance retention.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1472787/000095017024017418/faf-20231231.htm", "2024-02-21", None),

    ("sec_hanesbrands_2022_ransomware", "Hanesbrands Inc.", "0001359841", "US",
     "manufacturing", True, "ransomware", "2022-05", "month",
     "Ransomware attack disrupting order fulfilment at an apparel manufacturer.",
     [("direct_cost", 15_509_000, "USD", "net_of_insurance", "six months ended 2022-07-02", "final", "consolidated statements denominated in thousands; a later filing states the same figure as '$15 million'",
       "During the quarter and six months ended July 2, 2022, the Company incurred costs of $ 15,509 , net of expected insurance recoveries, related to the ransomware attack."),
      ("insurance_recovery", 5_562_000, "USD", "gross", "six months ended 2023-07-01", "final", "consolidated statements denominated in thousands",
       "During the quarter and six months ended July 1, 2023, the Company received business interruption insurance proceeds of $ 5,562")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1359841/000135984123000041/hbi-20230701.htm", "2023-08-10", None),

    ("sec_henry_schein_2023_cyber_incident", "HENRY SCHEIN INC", "0001000228", "US",
     "healthcare", True, "unspecified_cyber_incident", "2023-10", "month",
     "October 2023 cybersecurity incident at a healthcare products distributor.",
     [("direct_cost", 11_000_000, "USD", "gross", "year ended 2023-12-30", "provisional", None,
       "During the year ended December 30, 2023, we incurred $ 11 million of expenses directly related to the cybersecurity incident, mostly consisting of professional fees.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1000228/000100022824000011/form10k20231230.htm", "2024-02-28",
     "The same filing states a $60 million insurance policy after a $5 million retention. That is coverage, not loss, and is deliberately not recorded as an amount."),

    ("sec_hillman_2023_cyber_incident", "Hillman Solutions Corp.", "0001822492", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2023", "year",
     "Cybersecurity incident at a hardware and fastener distributor.",
     [("direct_cost", 1_000_000, "USD", "net_of_insurance", "fiscal 2023", "final", None,
       "In 2023, the Cybersecurity Incident related costs net of an expected insurance receivable totaled $1.0 million.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1822492/000182249225000050/hlmn-20241228.htm", "2025-02-20", None),

    ("sec_irhythm_2026_cyber_incident", "iRhythm Holdings, Inc.", "0001388658", "US",
     "healthcare", True, "unspecified_cyber_incident", "2026", "year",
     "Cybersecurity incident at a cardiac monitoring company.",
     [("direct_cost", 700_000, "USD", "not_stated", "six months ended 2026-06-30", "provisional", None,
       "For the three and six months ended June 30, 2026, we incurred $0.7 million related to the Cybersecurity Incident.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1388658/000138865826000072/irtc-20260630.htm", "2026-08-06", None),

    ("sec_johnson_controls_2023_ransomware", "Johnson Controls International plc", "0000833444", "IE",
     "manufacturing", True, "ransomware", "2023-09", "month",
     "Ransomware incident disrupting order entry and billing at a building-systems manufacturer.",
     [("total_event_impact", 30_000_000, "USD", "gross", "fiscal 2023", "provisional", None,
       "Lost and deferred revenues and expenses related to the cybersecurity incident adversely impacted fiscal 2023 net income by approximately $30 million, or approximately $0.04 per diluted share.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/833444/000083344423000048/jci-20230930.htm", "2023-12-14",
     "A net-income impact combining lost revenue and expense, not a direct-cost figure."),

    ("sec_key_tronic_2024_cyber_incident", "KEY TRONIC CORP", "0000719733", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2024-05", "month",
     "Cybersecurity incident late in fiscal 2024 at a contract electronics manufacturer.",
     [("direct_cost", 2_300_000, "USD", "not_stated", "fiscal year 2024", "final", None,
       "During fiscal year 2024, we incurred expenses related to a cybersecurity incident late in the year of approximately $2.3 million.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/719733/000071973324000113/ktcc-20240629.htm", "2024-10-15", None),

    ("sec_krispy_kreme_2024_cyber_incident", "Krispy Kreme, Inc.", "0001857154", "US",
     "food_and_beverage", True, "unspecified_cyber_incident", "2024-11", "month",
     "November 2024 cybersecurity incident disrupting online ordering.",
     [("direct_cost", 3_100_000, "USD", "gross", "fiscal 2024", "provisional", None,
       "Fiscal 2024 consists primarily of $3.1 million in costs related to remediation of the 2024 Cybersecurity Incident, including fees for cybersecurity experts and other advisors."),
      ("revenue_impact", 11_000_000, "USD", "gross", "fiscal 2024", "provisional", None,
       "segment in an amount of $11 million related to the incident with a corresponding estimated $10 million impact on Adjusted EBITDA")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1857154/000185715425000013/dnut-20241229.htm", "2025-02-27", None),

    ("sec_lee_enterprises_2025_cyber_incident", "LEE ENTERPRISES, Inc", "0000058361", "US",
     "media", True, "unspecified_cyber_incident", "2025-02", "month",
     "February 2025 cyber incident disrupting publishing and distribution operations.",
     [("direct_cost", 3_100_000, "USD", "gross", "nine months ended 2025-06-29", "provisional", None,
       "During the nine months ended June 29, 2025, the Company incurred $ 3.1 million of expenses related to the Cyber Incident.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/58361/000162828025039251/lee-20250629.htm", "2025-08-08", None),

    ("sec_livanova_2023_cyber_incident", "LivaNova PLC", "0001639691", "GB",
     "healthcare", True, "unspecified_cyber_incident", "2023-11", "month",
     "Cybersecurity incident at a medical device manufacturer.",
     [("direct_cost", 10_800_000, "USD", "gross", "through 2024-09-30", "provisional", None,
       "Through September 30, 2024, LivaNova incurred direct costs totaling $ 10.8 million in connection with this cybersecurity incident, including $ 2.5 million and $ 8.2 million during the three and nine months ended September 30, 2024, respectively.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1639691/000163969124000134/livn-20240930.htm", "2024-10-31", None),

    ("sec_loandepot_2024_cyber_incident", "loanDepot, Inc.", "0001831631", "US",
     "financial_services", True, "data_breach", "2024-01", "month",
     "January 2024 cybersecurity incident at a mortgage lender, followed by class-action litigation.",
     [("direct_cost", 22_800_000, "USD", "net_of_insurance", "nine months ended 2024-09-30", "provisional", None,
       "During the nine months ended September 30, 2024, the Company recognized $ 22.8 million of expenses related to the Cybersecurity Incident, net of insurance recoveries, which includes an accrual of $ 25.0 million in connection with class action litigation related to the C")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1831631/000183163124000285/ldi-20240930.htm", "2024-11-12",
     "Net of insurance and inclusive of a $25.0 million litigation accrual, so the gross direct cost is not recoverable from this figure."),

    ("sec_masimo_2025_cyber_incident", "MASIMO CORP", "0000937556", "US",
     "healthcare", True, "unspecified_cyber_incident", "2025-04", "month",
     "Cybersecurity incident affecting manufacturing and order processing at a medical device maker.",
     [("direct_cost", 5_500_000, "USD", "gross", "nine months ended 2025-09-27", "provisional", None,
       "For the nine months ended September 27, 2025, we incurred approximately $5.5 million, in selling, general and administrative expenses, related to the cybersecurity incident, offset by an insurance reimbursement of approximately $4.3 million."),
      ("insurance_recovery", 4_300_000, "USD", "gross", "nine months ended 2025-09-27", "provisional", None,
       "offset by an insurance reimbursement of approximately $4.3 million")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/937556/000093755625000161/masi-20250927.htm", "2025-11-04", None),

    ("sec_maximus_2023_moveit", "MAXIMUS, INC.", "0001032220", "US",
     "business_services", True, "data_breach", "2023-05", "month",
     "Data breach via a third-party file transfer product, affecting government programme participants.",
     [("direct_cost", 29_300_000, "USD", "gross", "fiscal year 2023", "provisional", None,
       "Our costs for the year ended September 30, 2023, include a $29.3 million expense incurred in the second half of the year for our best estimate of the investigation and remediation costs of a previously disclosed cybersecurity incident.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1032220/000103222023000096/mms-20230930.htm", "2023-11-16", None),

    ("sec_mueller_water_2023_cyber_incident", "Mueller Water Products, Inc.", "0001350593", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2023-10", "month",
     "Cybersecurity incident affecting manufacturing operations at a water infrastructure maker.",
     [("direct_cost", 1_500_000, "USD", "not_stated", "fiscal 2024", "final", None,
       "In fiscal 2024, we incurred approximately $1.5 million of expenses related to the cybersecurity incidents.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1350593/000135059324000079/mwa-20240930.htm", "2024-11-20", None),

    ("sec_prog_holdings_2023_cyber_incident", "PROG Holdings, Inc.", "0001808834", "US",
     "financial_services", True, "data_breach", "2023-09", "month",
     "Cybersecurity incident at a lease-to-own financial technology group.",
     [("direct_cost", 2_900_000, "USD", "gross", "aggregate since the incident, to 2024-03-31", "provisional", None,
       "During the three months ended March 31, 2024, the Company incurred $ 0.1 million for costs related to the cybersecurity incident, resulting in aggregate expenses of $ 2.9 million since the incident occurred.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1808834/000180883424000064/prg-20240331.htm", "2024-04-24", None),

    ("sec_sinclair_2021_ransomware", "SINCLAIR BROADCAST GROUP INC", "0000912752", "US",
     "media", True, "ransomware", "2021-10-17", "day",
     "Ransomware incident disrupting broadcast operations and advertising delivery.",
     [("revenue_impact", 63_000_000, "USD", "gross", "fourth quarter 2021", "final", None,
       "The cybersecurity incident identified on October 17, 2021 resulted in the loss in the fourth quarter of 2021 of approximately $63 million of advertising revenue, primarily related to our broadcast segment"),
      ("total_event_impact", 20_000_000, "USD", "net_of_insurance", "through the date of filing", "final", None,
       "the Company estimates that the cyber incident has resulted in approximately $20 million of unrecoverable net loss through the")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/912752/000091275223000010/sbgi-20221231.htm", "2023-03-01",
     "The $63M revenue loss and the $20M unrecoverable net loss are different constructs and must not be summed. Pre-dates the SEC cyber disclosure rule."),

    ("sec_sonic_automotive_2024_cdk_outage", "SONIC AUTOMOTIVE INC", "0001043509", "US",
     "retail", True, "third_party_outage", "2024-06", "month",
     "Business disruption from the CDK Global outage, a third-party dealer management system.",
     [("total_event_impact", 30_000_000, "USD", "gross", "quarter ended 2024-06-30", "provisional", None,
       "We estimate the disruption from the CDK outage negatively impacted reported income before taxes by approximately $30.0 million during the quarter ended June 30, 2024, which includes approximately $11.6 million in additional compensation expenses incurred as a result of")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1043509/000104350924000065/sah-20240630.htm", "2024-08-08",
     "The incident occurred at a third party; the loss is the filer's. Useful precisely because third-party outage loss is rarely quantified per-company."),

    ("sec_southstate_2024_cyber_incident", "SouthState Corp", "0000764038", "US",
     "financial_services", True, "unspecified_cyber_incident", "2024", "year",
     "Cybersecurity incident described by the filer as an isolated event.",
     [("direct_cost", 3_500_000, "USD", "not_stated", "2024 to 2024-06-30", "provisional", None,
       "Of the $4.0 million in 2024, approximately $3.5 million pertains to one-time costs associated with the cybersecurity incident, which was identified as an isolated event as previously disclosed by the Company.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/764038/000155837024010655/ssb-20240630x10q.htm", "2024-08-02",
     "A separate sentence in the same filing cites approximately $7.9 million of one-time incident costs for a different period; the periods are not reconciled in the filing, so only the explicitly-scoped figure is recorded."),

    ("sec_surmodics_2025_cyber_incident", "SURMODICS INC", "0000924717", "US",
     "healthcare", True, "unspecified_cyber_incident", "2025", "year",
     "Cyber incident at a medical device coatings company.",
     [("direct_cost", 1_900_000, "USD", "gross", "nine months ended 2025-06-30", "provisional", None,
       "During the three and nine months ended June 30, 2025, the Company incurred $ 1.9 million of Cyber Incident response costs of which $ 1.7 million is expected to be recovered under its cyber insurance policy."),
      ("insurance_recovery", 1_700_000, "USD", "gross", "expected, at 2025-06-30", "provisional", None,
       "of which $ 1.7 million is expected to be recovered under its cyber insurance policy")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/924717/000095017025105477/srdx-20250630.htm", "2025-08-08",
     "The insurance recovery is expected, not received."),

    ("sec_tempur_sealy_2023_cyber_incident", "TEMPUR SEALY INTERNATIONAL, INC.", "0001206264", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2023-07-23", "day",
     "Cybersecurity incident causing a temporary shutdown of operations at a bedding manufacturer.",
     [("direct_cost", 14_300_000, "USD", "gross", "year ended 2023-12-31", "final", None,
       "As a result of the cybersecurity incident, we incurred $14.3 million of costs in connection with this event.")],
     "10-K", "https://www.sec.gov/Archives/edgar/data/1206264/000120626424000050/tpx-20231231.htm", "2024-02-16",
     "Incident pre-dates the SEC cyber disclosure rule's December 2023 effective date; no Item 1.05 filing exists for it."),

    ("sec_tenet_healthcare_2022_cyber_incident", "TENET HEALTHCARE CORP", "0000070318", "US",
     "healthcare", True, "unspecified_cyber_incident", "2022-04", "month",
     "Cybersecurity incident disrupting hospital operations.",
     [("insurance_recovery", 31_000_000, "USD", "gross", "six months ended 2023-06-30", "final", None,
       "We received $ 31 million of insurance recoveries related to the Cybersecurity Incident during the six months ended June 30, 2023;")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/70318/000007031823000041/thc-20230630.htm", "2023-07-31",
     "A recovery only. The filing does not state the gross loss, so this record says nothing about event cost."),

    ("sec_ttec_2022_cyber_incident", "TTEC Holdings, Inc.", "0001013880", "US",
     "business_services", True, "ransomware", "2021-09", "month",
     "Cybersecurity incident at a customer-experience outsourcing provider.",
     [("insurance_recovery", 5_100_000, "USD", "gross", "three months ended 2023-03-31", "final", None,
       "The operating income increased primarily due to increased revenue and a net reimbursement from insurance of $5.1 million from the cybersecurity incident.")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1013880/000155837023008307/ttec-20230331x10q.htm", "2023-05-05",
     "A net insurance reimbursement, not a loss. The filing does not state the gross cost."),

    ("sec_united_natural_foods_2025_cyber_incident", "UNITED NATURAL FOODS INC", "0001020859", "US",
     "wholesale", True, "unspecified_cyber_incident", "2025-06", "month",
     "Cybersecurity incident disrupting distribution and order fulfilment at a grocery wholesaler.",
     [("direct_cost", 14_000_000, "USD", "gross", "first quarter fiscal 2026", "provisional", None,
       "During the first quarter of fiscal 2026, the Company recognized $ 14 million of incremental costs and charges related to the Cybersecurity Incident, of which $ 13 million is included in Gross profit and $ 1 million is included in Operating expenses"),
      ("insurance_recovery", 10_000_000, "USD", "gross", "first quarter fiscal 2026", "provisional", None,
       "In the first quarter of fiscal 2026, the Company received $ 10 million in cybersecurity insurance proceeds related to the Cybersecurity Incident the Company experienced in the fourth quarter of fiscal 2025")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/1020859/000102085925000065/unfi-20251101.htm", "2025-12-02",
     "A prior-period filing reported approximately $26 million of incremental costs for the fourth quarter of fiscal 2025; this record covers the following quarter only."),

    ("sec_west_pharmaceutical_2026_cyber_incident", "WEST PHARMACEUTICAL SERVICES INC", "0000105770", "US",
     "manufacturing", True, "unspecified_cyber_incident", "2026-05", "month",
     "May 2026 cyber incident causing production downtime at a drug packaging manufacturer.",
     [("revenue_impact", 7_000_000, "USD", "gross", "three months ended 2026-06-30", "provisional", None,
       "our revenue growth being negatively impacted by approximately $7 million from production downtime associated with the Company's May 2026 cyber incident")],
     "10-Q", "https://www.sec.gov/Archives/edgar/data/105770/000010577026000099/wst-20260630.htm", "2026-07-23", None),
]


def q(text):
    """YAML double-quoted scalar."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    out = [
        "# Loss-event registry — SEC filings, 2023-2026",
        "#",
        "# Governed by schemas/loss_event_schema.json (ADR-0012, superseding ADR-0005).",
        "# Generated from docs/internal/research/loss_event_extraction.py, whose hand-verified",
        "# table is the verification ADR-0012 requires. Do not hand-edit this file: change the",
        "# table and regenerate, so the record and its verification never drift apart.",
        "#",
        "# These are documented events. They are tail and defensibility evidence only: never",
        "# aggregate them into a central tendency, and never read an exceedance probability",
        "# out of them.",
        "",
        "events:",
    ]
    for (eid, name, cik, country, industry, listed, threat, date, precision,
         desc, amounts, filing_type, url, filing_date, extra) in EVENTS:
        limits = CORPUS_LIMITS if not extra else f"{extra} {CORPUS_LIMITS}"
        out += [
            f"  - id: {eid}",
            "    entity:",
            f"      name: {q(name)}",
            f"      cik: {q(cik)}",
            f"      country: {q(country)}",
            f"      industry: {q(industry)}",
            f"      listed: {str(listed).lower()}",
            "    event:",
            f"      description: {q(desc)}",
            f"      threat: {threat}",
            f"      date: {q(date)}",
            f"      date_precision: {precision}",
            "    amounts:",
        ]
        for (atype, value, currency, basis, period, status, units_from, cited) in amounts:
            out += [
                f"      - type: {atype}",
                f"        value: {value}",
                f"        currency: {currency}",
                f"        basis: {basis}",
                f"        period: {q(period)}",
                f"        status: {status}",
            ]
            if units_from:
                out.append(f"        units_resolved_from: {q(units_from)}")
            out.append(f"        cited_line: {q(cited)}")
        out += [
            "    source:",
            f"      filing_type: {filing_type}",
            f"      url: {q(url)}",
            f"      filing_date: {q(filing_date)}",
            f"      filer_name: {q(name)}",
            f"    extraction_date: {q(EXTRACTED)}",
            "    verification:",
            "      method: machine_candidate_human_confirmed",
            f"      verified_by: {q(VERIFIER)}",
            "      candidate_source: \"edgar_corpus_census.py lane C/A\"",
            f"    limitations: {q(limits)}",
        ]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
