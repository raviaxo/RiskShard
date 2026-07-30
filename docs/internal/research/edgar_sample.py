#!/usr/bin/env python3
"""Sample Item 1.05 filers and measure how many ever quantify the cost.

Decides ADR-0005: if few filings ever produce a number, the registry is overhead.
Method: list Item 1.05 8-K filers, then for each follow their subsequent 10-Q/10-K
and look for a monetary figure in the same neighbourhood as cyber-incident language.
"""
import json
import re
import time
import urllib.request

UA = "RiskShard research s.alonso.rodriguez@gmail.com"
CYBER = re.compile(r"cyber(?:security)?\s+incident|the\s+Incident\b", re.I)
MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand)?", re.I)


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        import gzip
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "ignore")


def item105_filers(limit=40):
    """Unique (cik, name, date) that filed an Item 1.05 8-K."""
    seen, out = set(), []
    for start in range(0, 100, 10):
        url = ("https://efts.sec.gov/LATEST/search-index?q=%22Item+1.05%22"
               f"&forms=8-K&from={start}")
        try:
            hits = json.loads(get(url))["hits"]["hits"]
        except Exception as exc:
            print(f"  search page {start} failed: {exc}")
            break
        if not hits:
            break
        for h in hits:
            src = h["_source"]
            cik = (src.get("ciks") or ["?"])[0]
            name = (src.get("display_names") or ["?"])[0].split("  (")[0]
            if cik in seen:
                continue
            seen.add(cik)
            out.append((cik, name, src.get("file_date")))
            if len(out) >= limit:
                return out
        time.sleep(0.3)
    return out


def later_reports(cik, after, want=("10-Q", "10-K"), cap=2):
    """Primary-document URLs for periodic reports filed after the incident 8-K."""
    url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    try:
        recent = json.loads(get(url))["filings"]["recent"]
    except Exception:
        return []
    rows = []
    for form, date, acc, doc in zip(recent["form"], recent["filingDate"],
                                    recent["accessionNumber"], recent["primaryDocument"]):
        if form in want and date >= after:
            acc_plain = acc.replace("-", "")
            rows.append((form, date,
                         f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_plain}/{doc}"))
    rows.sort(key=lambda r: r[1])
    return rows[:cap]


def quantified(text):
    """A money figure within ~700 chars of cyber-incident language."""
    flat = re.sub(r"<[^>]+>", " ", text)
    flat = re.sub(r"&[a-z]+;", " ", flat)
    flat = re.sub(r"\s+", " ", flat)
    for m in CYBER.finditer(flat):
        window = flat[max(0, m.start() - 700): m.start() + 700]
        money = MONEY.findall(window)
        # ignore bare "$0" style noise and require a plausible magnitude
        money = [x for x in money if re.search(r"\d", x) and x.strip() not in ("$0", "$ 0")]
        if money:
            return money[:3], window[:300]
    return None, None


def main():
    filers = item105_filers(limit=40)
    print(f"Item 1.05 filers discovered: {len(filers)}\n")
    sample = filers[:20]
    hits = 0
    for i, (cik, name, date) in enumerate(sample, 1):
        reports = later_reports(cik, date)
        found, snippet, where = None, None, None
        for form, fdate, url in reports:
            try:
                text = get(url)
            except Exception:
                continue
            money, snip = quantified(text)
            if money:
                found, snippet, where = money, snip, f"{form} {fdate}"
                break
            time.sleep(0.25)
        status = "QUANTIFIED" if found else ("no figure" if reports else "no later report")
        if found:
            hits += 1
        print(f"{i:2}. {name[:40]:40} 8-K {date}  -> {status}")
        if found:
            print(f"      {where}: {', '.join(found)}")
            print(f"      ...{snippet[:200].strip()}...")
        time.sleep(0.3)
    print(f"\nRESULT: {hits}/{len(sample)} sampled filers quantified a cost in a later periodic report")


if __name__ == "__main__":
    main()
