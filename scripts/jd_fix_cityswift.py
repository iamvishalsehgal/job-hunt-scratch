#!/usr/bin/env python3
"""Re-fetch the CitySwift Greenhouse posting and write a clean jd.md."""
import html
import json
import re
import urllib.request

OUT = "/home/ubuntu/.hermes/profiles/vishal/workspace/applications/cityswift-analytics-engineer/jd.md"
URL = "https://boards-api.greenhouse.io/v1/boards/cityswift/jobs?content=true"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace"))
job = [j for j in data["jobs"] if j.get("title") == "Analytics Engineer"][0]

raw = html.unescape(job["content"])
raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
raw = re.sub(r"<li[^>]*>", "\n* ", raw, flags=re.I)
raw = re.sub(r"</(p|div|h1|h2|h3|h4|ul|ol|li|br|tr)>", "\n", raw, flags=re.I)
raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
raw = re.sub(r"<[^>]+>", " ", raw)
raw = html.unescape(raw)
raw = re.sub(r"[ \t\u00a0]+", " ", raw)
raw = re.sub(r"\n\s*\n+", "\n\n", raw).strip()

head = ("# Analytics Engineer - CitySwift, Galway Ireland\n"
        "Source: https://cityswift.com/job-post/?gh_jid=%s (Greenhouse board cityswift, "
        "employer page https://cityswift.com/careers)\n\n" % job["id"])
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(head + raw + "\n")
print("wrote", OUT, len(head + raw), "bytes")
print(raw[:300].replace("\n", " "))
