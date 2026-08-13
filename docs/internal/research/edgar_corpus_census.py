#!/usr/bin/env python3
"""Census the EDGAR cyber-loss corpus: how many quantified, attributable events exist?

Sizes the ADR-0005 registry decision. The feasibility sample behind that ADR
(`edgar_sample.py`, 2026-07-29) started from Item 1.05 8-K filings and followed each
filer to its next two periodic reports. It found 4 quantified events in 20 filers and
flagged two things it had not measured: how far Item 1.05 undercounts, and how many
filings ever carry a number.

This census answers both, and adds a discovery lane the original did not have.

  Lane A  Item 1.05 8-K filers, followed to subsequent 10-Q/10-K.
          The original method, run over the whole discovered set rather than 20.

  Lane B  8-K filings mentioning "cybersecurity incident" at all. Counted, not
          crawled: it is a contaminated upper bound (boilerplate, other companies'
          incidents, risk-factor prose) and its only job here is to size how far an
          Item 1.05 query undercounts.

  Lane C  Periodic reports (10-K/10-Q) matched directly on high-precision cost
          phrases. This is the better method and it is new here. The phrases occur
          inside the cost sentence itself, so a hit is already the document holding
          the figure — no 8-K hop. It also reaches incidents that have no Item 1.05
          filing at all, including pre-rule ones (the rule took effect 2023-12-18).

Counting is sentence-level throughout: money, cyber-incident language and a cost word
in the SAME sentence (the `edgar_verify.py` method). The loose 700-character proximity
pass in `edgar_sample.py` was 50% wrong and is not used to count anything here.

Everything this prints is a CANDIDATE. ADR-0005 requires verification-assisted
extraction with every amount typed (gross loss vs insurance proceeds vs settlement)
before any of it becomes evidence.

Not product code: not wired into the CLI, not covered by the test suite. Kept so the
counts can be re-run and checked, per docs/internal/research/README.md.

Usage:
    python edgar_corpus_census.py discover
    python edgar_corpus_census.py quantify
    python edgar_corpus_census.py report
"""
import argparse
import gzip
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request

UA = "RiskShard research s.alonso.rodriguez@gmail.com"
CACHE = os.environ.get("EDGAR_CACHE", os.path.join(tempfile.gettempdir(), "riskshard_edgar_cache"))
START, END = "2023-01-01", "2026-08-13"

# Sentence-level matcher, from edgar_verify.py. All three must hit the same sentence.
CYBER = re.compile(r"cyber(?:security)?\s+incident|ransomware|the\s+Incident\b", re.I)
MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand)?", re.I)
COST = re.compile(r"cost|expense|charge|impact|loss|incurr|recover|insur|remediat|net\s+of", re.I)

# Lane C. High-precision because each phrase is the connective tissue of a cost
# sentence -- "we incurred $X <phrase>" -- rather than a topic mention. A bare
# "cybersecurity incident" search over 10-K/10-Q saturates the 10,000-hit cap on
# Item 1C governance boilerplate, which every 10-K now carries.
COST_PHRASES = [
    "related to the cybersecurity incident",
    "in connection with the cybersecurity incident",
    "as a result of the cybersecurity incident",
    "expenses related to the cybersecurity incident",
    "costs related to the cyber incident",
    "related to the cyber incident",
    "as a result of the cyber incident",
    "related to the ransomware attack",
    "in connection with the ransomware attack",
]


def get(url, timeout=90, retries=3):
    """Fetch with the SEC's required contact-identifying User-Agent, gzip-aware."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding")
            if enc == "gzip":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "ignore")
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    return ""


def cache_path(name):
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, name)


def load(name, default=None):
    p = cache_path(name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save(name, obj):
    with open(cache_path(name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


def search(query, forms, page_cap=200, count_only=False):
    """Full-text search hits. EFTS paginates 10 at a time and caps at 10,000."""
    q = urllib.parse.quote(f'"{query}"')
    base = (f"https://efts.sec.gov/LATEST/search-index?q={q}&forms={forms}"
            f"&dateRange=custom&startdt={START}&enddt={END}")
    out, start, total = [], 0, None
    while start < page_cap * 10:
        try:
            data = json.loads(get(f"{base}&from={start}"))
        except Exception as exc:
            print(f"    page from={start} failed: {exc}", file=sys.stderr)
            break
        if total is None:
            total = data["hits"]["total"]["value"]
            if count_only:
                return [], total
        hits = data["hits"]["hits"]
        if not hits:
            break
        out.extend(hits)
        start += 10
        if start >= total:
            break
        time.sleep(0.15)
    return out, total


def clean_name(src):
    names = src.get("display_names") or ["?"]
    return re.sub(r"\s{2,}\(.*$", "", names[0]).strip()


def doc_url(hit):
    """EFTS _id is '<accession>:<primary document>' -- gives the exact filed document."""
    src = hit["_source"]
    cik = (src.get("ciks") or [None])[0]
    if not cik:
        return None
    ident = hit.get("_id", "")
    if ":" not in ident:
        return None
    acc, doc = ident.split(":", 1)
    return (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{acc.replace('-', '')}/{doc}")


# --------------------------------------------------------------------------- discover

def discover():
    out = {"lanes": {}}

    print("[lane A] Item 1.05 8-K filings")
    hits_a, total_a = search("Item 1.05", "8-K")
    filers_a = {}
    for h in hits_a:
        src = h["_source"]
        cik = (src.get("ciks") or [None])[0]
        if not cik:
            continue
        d = src.get("file_date") or "9999-99-99"
        rec = filers_a.get(cik)
        if rec is None:
            filers_a[cik] = {"cik": cik, "name": clean_name(src), "date": d}
        elif d < rec["date"]:
            rec["date"] = d
    print(f"    {total_a} filings -> {len(filers_a)} unique filers")
    out["lanes"]["A"] = {"filings": total_a, "unique_filers": len(filers_a)}

    print('[lane B] 8-K mentioning "cybersecurity incident" (counted, not crawled)')
    _, total_b = search("cybersecurity incident", "8-K", count_only=True)
    print(f"    {total_b} filings (contaminated upper bound)")
    out["lanes"]["B"] = {"filings": total_b}

    print("[lane C] periodic reports matched on cost phrases")
    docs = {}
    per_phrase = {}
    for phrase in COST_PHRASES:
        hits, total = search(phrase, "10-K,10-Q")
        per_phrase[phrase] = total
        added = 0
        for h in hits:
            url = doc_url(h)
            if not url or url in docs:
                continue
            src = h["_source"]
            docs[url] = {"url": url, "cik": (src.get("ciks") or ["?"])[0],
                         "name": clean_name(src), "form": src.get("form"),
                         "date": src.get("file_date"), "phrase": phrase}
            added += 1
        print(f"    {total:>4} hits · {added:>3} new documents · \"{phrase}\"")
        time.sleep(0.2)
    ciks_c = {d["cik"] for d in docs.values()}
    print(f"    union: {len(docs)} unique documents across {len(ciks_c)} issuers")
    out["lanes"]["C"] = {"per_phrase": per_phrase, "unique_documents": len(docs),
                         "unique_issuers": len(ciks_c)}

    save("discovery.json", {"summary": out, "lane_a_filers": list(filers_a.values()),
                            "lane_c_docs": list(docs.values())})
    print("\nsaved discovery.json")
    return out


# -------------------------------------------------------------------------- quantify

def sentences(text):
    """Flatten HTML -- tables included -- to a sentence stream."""
    flat = re.sub(r"<[^>]+>", " ", text)
    flat = flat.replace("&#160;", " ").replace("&nbsp;", " ").replace("&#8217;", "'")
    flat = re.sub(r"&[a-z#0-9]+;", " ", flat)
    flat = re.sub(r"\s+", " ", flat)
    return re.split(r"(?<=[.;])\s+", flat)


def strict_hits(text, limit=4):
    out = []
    for s in sentences(text):
        if len(s) < 700 and CYBER.search(s) and MONEY.search(s) and COST.search(s):
            s = s.strip()
            if s not in out:
                out.append(s)
            if len(out) >= limit:
                break
    return out


def later_reports(cik, after, cap=4):
    url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    try:
        recent = json.loads(get(url))["filings"]["recent"]
    except Exception:
        return []
    rows = []
    for form, date, acc, doc in zip(recent["form"], recent["filingDate"],
                                    recent["accessionNumber"], recent["primaryDocument"]):
        if form in ("10-Q", "10-K") and date >= after and doc:
            rows.append((form, date, f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                                     f"{acc.replace('-', '')}/{doc}"))
    rows.sort(key=lambda r: r[1])
    return rows[:cap]


def quantify():
    disc = load("discovery.json")
    if not disc:
        sys.exit("run `discover` first")

    # ---- Lane C: the hit document already holds the sentence.
    res_c = load("results_c.json", {})
    docs = disc["lane_c_docs"]
    print(f"[lane C] {len(docs)} documents\n")
    for i, d in enumerate(docs, 1):
        if d["url"] in res_c:
            continue
        try:
            hits = strict_hits(get(d["url"]))
        except Exception as exc:
            hits = []
            print(f"    fetch failed: {d['name']}: {exc}", file=sys.stderr)
        rec = dict(d)
        rec["hits"] = hits
        res_c[d["url"]] = rec
        print(f"{i:4}/{len(docs)} {d['name'][:36]:36} {d['form']:5} "
              f"{'QUANTIFIED' if hits else '-'}")
        if hits:
            print(f"        {hits[0][:190]}")
        if i % 10 == 0:
            save("results_c.json", res_c)
        time.sleep(0.2)
    save("results_c.json", res_c)

    # ---- Lane A: the ADR-0005 method, over every discovered filer.
    res_a = load("results_a.json", {})
    filers = disc["lane_a_filers"]
    print(f"\n[lane A] {len(filers)} Item 1.05 filers\n")
    for i, f in enumerate(filers, 1):
        if f["cik"] in res_a:
            continue
        reports = later_reports(f["cik"], f["date"])
        rec = dict(f)
        rec.update({"reports_checked": len(reports), "hits": [], "source": None})
        for form, fdate, url in reports:
            try:
                hits = strict_hits(get(url))
            except Exception:
                continue
            if hits:
                rec["hits"] = hits
                rec["source"] = {"form": form, "date": fdate, "url": url}
                break
            time.sleep(0.2)
        res_a[f["cik"]] = rec
        state = "QUANTIFIED" if rec["hits"] else ("no figure" if reports else "no later report")
        print(f"{i:4}/{len(filers)} {f['name'][:36]:36} {state}")
        if i % 10 == 0:
            save("results_a.json", res_a)
        time.sleep(0.2)
    save("results_a.json", res_a)
    report()


# ---------------------------------------------------------------------------- report

def report():
    disc = load("discovery.json") or {}
    res_c = load("results_c.json", {})
    res_a = load("results_a.json", {})
    s = disc.get("summary", {}).get("lanes", {})

    print("\n" + "=" * 74)
    print("EDGAR CYBER-LOSS CORPUS CENSUS")
    print("=" * 74)
    print(f"  A  Item 1.05 8-K:            {s.get('A', {}).get('filings', '?')} filings, "
          f"{s.get('A', {}).get('unique_filers', '?')} filers")
    print(f"  B  8-K mentioning the term:  {s.get('B', {}).get('filings', '?')} filings "
          f"(contaminated upper bound)")
    print(f"  C  periodic-report phrases:  {s.get('C', {}).get('unique_documents', '?')} documents, "
          f"{s.get('C', {}).get('unique_issuers', '?')} issuers")

    c_rows = list(res_c.values())
    c_hit = [r for r in c_rows if r["hits"]]
    c_issuers = {r["cik"] for r in c_hit}
    a_rows = list(res_a.values())
    a_hit = [r for r in a_rows if r["hits"]]
    a_rep = [r for r in a_rows if r.get("reports_checked")]

    def pct(a, b):
        return f"{100.0 * len(a) / len(b):.0f}%" if b else "n/a"

    print("\n  LANE C (direct phrase match on periodic reports)")
    print(f"    documents checked:     {len(c_rows)}")
    print(f"    documents quantified:  {len(c_hit)}  ({pct(c_hit, c_rows)})")
    print(f"    DISTINCT ISSUERS with a quantified figure: {len(c_issuers)}")

    print("\n  LANE A (ADR-0005 method: Item 1.05 -> later periodic report)")
    print(f"    filers checked:        {len(a_rows)}")
    print(f"    had a later report:    {len(a_rep)}")
    print(f"    quantified:            {len(a_hit)}  "
          f"({pct(a_hit, a_rows)} of filers, {pct(a_hit, a_rep)} of those with a report)")
    print("    ADR-0005 comparison:   4/20 filers, ~27% of those with a report")

    a_ciks = {r["cik"] for r in a_hit}
    print(f"\n  UNION of distinct issuers with >=1 quantified figure: "
          f"{len(c_issuers | a_ciks)}")
    print(f"    found only by lane C (invisible to the ADR-0005 method): "
          f"{len(c_issuers - a_ciks)}")

    print("\n  --- candidates (verify each by opening the URL) ---")
    seen = set()
    for r in sorted(c_hit, key=lambda x: x["name"]):
        if r["cik"] in seen:
            continue
        seen.add(r["cik"])
        print(f"\n  {r['name']}  ({r['form']} {r['date']})")
        print(f"    {r['url']}")
        for h in r["hits"][:2]:
            print(f"    > {h[:300]}")
    for r in sorted(a_hit, key=lambda x: x["name"]):
        if r["cik"] in seen:
            continue
        seen.add(r["cik"])
        print(f"\n  {r['name']}  (8-K {r['date']} -> {r['source']['form']} {r['source']['date']})")
        print(f"    {r['source']['url']}")
        for h in r["hits"][:2]:
            print(f"    > {h[:300]}")

    print("\n  Every figure above is a CANDIDATE, not a registry entry. ADR-0005 requires")
    print("  verification-assisted extraction with every amount typed (gross loss vs")
    print("  insurance proceeds vs settlement vs fine) before any of it becomes evidence.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["discover", "quantify", "report"])
    a = ap.parse_args()
    print(f"cache: {CACHE}\n")
    {"discover": discover, "quantify": quantify, "report": report}[a.stage]()


if __name__ == "__main__":
    main()
