# What we can actually read — artifact readiness for the ADR-0015 audit

*Measured 2026-08-15. Re-runnable via
[`source_property_scan.py`](research/source_property_scan.py); the substance counts below
come from the same text extraction it uses.*

## The finding

The [source audit](../adr/0015-the-source-audit.md) can only answer a question about a source
by reading the source. Before reading 61 of them, the obvious check was whether we hold them.
We hold artifacts for 59. **We hold the actual document for 34.**

| | |
| --- | --- |
| registered sources | **61** |
| gathered artifacts on disk | **59** |
| artifacts that are the substantive document (≥1,500 words of extractable text) | **34** |
| artifacts that are a landing page, news summary or data-query response | **22** |
| artifacts in a format not readable as text here (xlsx, zip) | **3** |
| registered sources with no artifact at all | **2** |

## Why this mattered immediately

The first scan run hit **Cyentia IRIS**: three registered sources, each a 170–184 KB HTML file
containing **528–608 words**. That is a product page, not the report.

Cyentia's IRIS is the single most likely source in this corpus to publish a loss *distribution*
and an *exceedance* statement — it is the study built on the Advisen event set. Answering
"does Cyentia publish a distribution?" from a 528-word landing page would have produced a
confidently wrong entry about the most consequential source we hold, and the audit's own
verification rule would not have caught it: a human really did read the stored artifact.

**So the artifact being present is not the same as the source being readable**, and the audit
needed a state for that. `no_readable_artifact` was added to the schema, counted separately from
`unverified` in coverage, and printed separately by the doctor. *We have not read it* and
*we cannot read it* are different claims, and collapsing them lets a permanent gap look like a
backlog that effort will clear.

## The thin 22

Landing pages and news coverage standing in for the report — the audit cannot answer from these:

- **Cyentia** — `iris_2022` (528w), `iris_ransomware` (530w), `iris_2025` (608w)
- **IBM Cost of a Data Breach** — `ibm_canada_2025` (901w), `ibm_uk_2025` (1,267w), and
  `securitybrief_ibm_au_breach_costs_2026` (979w), which is secondary coverage by construction
- **Sophos State of Ransomware** — `australia_2025` (1,032w PDF), `manufacturing_2024` (1,312w),
  `financial_services_2024` (1,387w)
- **AFP Payments Fraud** — `2025` (1,443w), `2026` (1,279w)
- **Others** — CSA Singapore health report (791w PDF), CESIN barometre (1,498w PDF), MYOB (849w),
  Cybersecurity Insiders insider threat (857w), Interos (611w), ICO self-reported breaches (269w),
  CNIL GDPR Article 83 (831w), AFP BEC case (1,111w), Arup deepfake via CNN (1,346w)

Some of these are *legitimately* short — the ICO page is a statistics table, the CNIL page is a
legal article, the Arup case is a news report of a single event, and Eurostat (126w) and SingStat
(173w) are JSON query responses that are exactly what we asked for. **Short is not the defect;
being a pointer to the document rather than the document is.** Each will be marked when it is
adjudicated, not in bulk from a word count.

## The unreadable 3 and the missing 2

`census_susb_2022` (.xlsx), `npa_japan_cyber_threats_2025_statistics` (.xlsx) and
`statcan_cscsc_incident_types_22100076` (.zip) are statistical tables. They are readable with the
right tool rather than genuinely blocked, and they are data releases rather than reports — the four
audit questions apply differently to a table than to a study, which is worth resolving before
answering them.

`first_epss_data_stats` and `asd_annual_cyber_threat_report_2024_2025` are registered with no
gathered artifact.

## What this costs the audit

**34 of 61 sources are answerable today**, and the audit's coverage number must reflect that rather
than implying the remaining 27 are merely un-started. The strongest claim available without
obtaining more documents is one over 34 named sources, with 22 recorded as *held only as a
pointer* and stated as such wherever the claim appears.

Obtaining the Cyentia IRIS reports, the IBM Cost of a Data Breach report and the full Sophos State
of Ransomware would move the audit further than any other work available to it, because those three
are both the most cited and the most likely to publish exactly the properties in question.
