#!/usr/bin/env python3
"""FareHarbor liveness: job-boards page content check."""
import re, subprocess, html
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
raw = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "30",
                      "https://job-boards.greenhouse.io/fareharbor/jobs/8571117002"],
                     capture_output=True, text=True, timeout=45).stdout
txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
txt = re.sub(r"(?s)<[^>]+>", " ", txt)
txt = re.sub(r"\s+", " ", html.unescape(txt))
print("len:", len(txt))
print(txt[:600])
for pat in ["no longer", "not found", "closed", "Lead, Data Analytics", "Apply", "expired"]:
    m = re.findall(r".{0,60}" + pat + r".{0,60}", txt, re.I)[:2]
    print(pat, "->", m)
