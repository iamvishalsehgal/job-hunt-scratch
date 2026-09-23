#!/usr/bin/env python3
"""Tier-1 EU (DE, IE) LinkedIn guest-API sweep through the response cache.

8 keywords x 2 countries x 2 offsets = 32 cached fetches.
Writes raw bodies + a card manifest. Never invents data: a non-zero
discovery_cache exit is recorded as a failed query.
"""
import json
import os
import re
import subprocess
import sys

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
OUT = "/home/ubuntu/job-hunt-scratch"
RAW = os.path.join(OUT, "eu_raw")
os.makedirs(RAW, exist_ok=True)

KEYWORDS = [
    "Data Engineer",
    "Analytics Engineer",
    "Data Platform Engineer",
    "Azure Data Engineer",
    "Databricks Engineer",
    "Snowflake Engineer",
    "dbt",
    "Knowledge Graph Engineer",
]
COUNTRIES = [("DE", "Germany"), ("IE", "Ireland")]
OFFSETS = [0, 25]

CARD_RE = re.compile(
    r'data-entity-urn="urn:li:jobPosting:(\d+)".*?'
    r'<a class="base-card__full-link[^"]*"\s+href="([^"]+)"(.*?)'
    r'</li>',
    re.S,
)
TITLE_RE = re.compile(r'base-search-card__title[^>]*>\s*(.*?)\s*</h3>', re.S)
COMPANY_RE = re.compile(r'base-search-card__subtitle.*?<a[^>]*>\s*(.*?)\s*</a>', re.S)
LOC_RE = re.compile(r'job-search-card__location[^>]*>\s*(.*?)\s*</span>', re.S)
DATE_RE = re.compile(r'job-search-card__listdate[^>]*datetime="([\d-]+)"', re.S)


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
          .replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", s).strip()


def main():
    manifest = []
    cards = []
    for kw in KEYWORDS:
        for cc, loc in COUNTRIES:
            for off in OFFSETS:
                url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                       "?keywords=" + kw.replace(" ", "%20") +
                       "&location=" + loc + "&start=" + str(off))
                cp = subprocess.run(
                    ["python3", os.path.join(WS, "tools/discovery_cache.py"), "fetch",
                     "--url", url, "--candidate", "vishal"],
                    capture_output=True, text=True, cwd=WS, timeout=120,
                )
                body = cp.stdout
                n = 0
                if cp.returncode == 0:
                    i = body.find("<!DOCTYPE")
                    if i < 0:
                        i = body.find("<li")
                    html = body[i:] if i >= 0 else ""
                    path = os.path.join(RAW, "%s_%s_%d.html" % (
                        kw.replace(" ", "-").lower(), cc, off))
                    with open(path, "w") as fh:
                        fh.write(html)
                    for m in CARD_RE.finditer(html):
                        jid, href, tail = m.group(1), m.group(2), m.group(3)
                        t = TITLE_RE.search(tail)
                        c = COMPANY_RE.search(tail)
                        l = LOC_RE.search(tail)
                        d = DATE_RE.search(tail)
                        cards.append({
                            "id": jid,
                            "title": clean(t.group(1)) if t else "",
                            "company": clean(c.group(1)) if c else "",
                            "location": clean(l.group(1)) if l else "",
                            "url": href.split("?")[0],
                            "posted": d.group(1) if d else "",
                            "kw": kw,
                            "loc_req": loc,
                        })
                        n += 1
                manifest.append({"kw": kw, "country": cc, "offset": off,
                                 "rc": cp.returncode, "cards": n})
                print("%s|%s|%d rc=%d cards=%d" % (kw, cc, off, cp.returncode, n),
                      flush=True)
    with open(os.path.join(OUT, "eu_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    with open(os.path.join(OUT, "eu_cards.json"), "w") as fh:
        json.dump(cards, fh, indent=1)
    ok = sum(1 for m in manifest if m["rc"] == 0)
    print("QUERIES %d ok %d failed %d" % (len(manifest), ok, len(manifest) - ok))
    print("RAW CARDS %d unique ids %d" % (len(cards), len({c["id"] for c in cards})))


if __name__ == "__main__":
    sys.exit(main())
