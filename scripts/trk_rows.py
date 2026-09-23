#!/usr/bin/env python3
"""Extract every tracker row's company field from build_tracker.py and test finalists."""
import json
import os
import re

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
SCRATCH = "/home/ubuntu/job-hunt-scratch"
TXT = open(os.path.join(WS, "build_tracker.py"), errors="replace").read()
pat = re.compile(r'\[\s*"(\d+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"')
rows = [(m.group(1), m.group(2).replace('\\"', '"'), m.group(3).replace('\\"', '"'),
         m.group(4).replace('\\"', '"')) for m in pat.finditer(TXT)]
print("TRACKER ROWS PARSED: %d" % len(rows))
comps = sorted({c.strip() for _, c, _, _ in rows})
print("DISTINCT COMPANIES: %d" % len(comps))
open(os.path.join(SCRATCH, "tracker_companies.json"), "w").write(json.dumps(comps, indent=1))

FINAL = ["Mastercard", "Musgrave", "Euronext", "Workday", "Version 1", "Creditsafe",
         "CitySwift", "Block Labs", "DoiT", "GEA", "Primer", "Intact", "JPMorgan",
         "Fulcrum", "Sandbox", "Intact Insurance"]
for f in FINAL:
    hits = [(n, c, ro, st) for n, c, ro, st in rows if f.lower() in c.lower()]
    print("-- %-20s -> %d row hit(s)" % (f, len(hits)))
    for h in hits[:5]:
        print("     row %s | %s | %s" % (h[0], h[1], h[2][:70]))
