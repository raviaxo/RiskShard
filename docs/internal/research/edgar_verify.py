#!/usr/bin/env python3
"""Stricter re-check of the six apparent hits: money and cyber language in the SAME sentence."""
import gzip
import json
import re
import time
import urllib.request

UA = "RiskShard research s.alonso.rodriguez@gmail.com"
CYBER = re.compile(r"cyber(?:security)?\s+incident|ransomware|CDK\s+outage|the\s+Incident\b", re.I)
MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s*(million|billion|thousand)?", re.I)
# words that mark the number as an actual cost of the incident
COST = re.compile(r"cost|expense|charge|impact|loss|incurr|recover|insur|remediat|net\s+of", re.I)

TARGETS = [
    ("UNITED NATURAL FOODS", "0001020859", "10-K"),
    ("DATA I/O CORP", "0000351998", "10-K"),
    ("SONIC AUTOMOTIVE", "0001043509", "10-Q"),
    ("CareCloud", "0001582982", "10-Q"),
    ("LEE ENTERPRISES", "0000058361", "10-Q"),
    ("F5 INC", "0001048695", "10-K"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        enc = r.headers.get("Content-Encoding")
    if enc == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "ignore")


def latest(cik, form):
    data = json.loads(get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"))
    rec = data["filings"]["recent"]
    for f, d, acc, doc in zip(rec["form"], rec["filingDate"], rec["accessionNumber"], rec["primaryDocument"]):
        if f == form:
            return d, f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{doc}"
    return None, None


def sentences(text):
    flat = re.sub(r"<[^>]+>", " ", text)
    flat = flat.replace("&#160;", " ").replace("&nbsp;", " ").replace("&#8217;", "'")
    flat = re.sub(r"&[a-z#0-9]+;", " ", flat)
    flat = re.sub(r"\s+", " ", flat)
    return re.split(r"(?<=[.;])\s+", flat)


for name, cik, form in TARGETS:
    date, url = latest(cik, form)
    if not url:
        print(f"{name}: no {form} found\n")
        continue
    try:
        text = get(url)
    except Exception as exc:
        print(f"{name}: fetch failed {exc}\n")
        continue
    good = []
    for s in sentences(text):
        if CYBER.search(s) and MONEY.search(s) and COST.search(s) and len(s) < 700:
            good.append(s.strip())
    print(f"=== {name}  ({form} {date})  strict matches: {len(good)}")
    for s in good[:2]:
        print(f"    {s[:400]}")
    print()
    time.sleep(0.4)
