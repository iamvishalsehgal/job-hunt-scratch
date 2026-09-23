#!/usr/bin/env python3
"""Print bullet/requirement lines for the 6 shortlisted JDs (context-lean review)."""
import json
import os

SCRATCH = "/home/ubuntu/job-hunt-scratch"
rows = {r["company"]: r for r in json.load(open(os.path.join(SCRATCH, "eu_shortlist.json")))}
for comp in ["version-1", "doit", "gea-group", "primer", "cityswift", "sandbox-interactive",
             "workday", "mastercard", "block-labs"]:
    r = rows[comp]
    body = open(r["path"], errors="replace").read().split("## Job description", 1)[-1]
    print("=" * 100)
    print("### %s | %s" % (comp, r["role"]))
    for line in body.splitlines():
        s = line.replace("\u2022", "*").replace("\u2013", "-").strip()
        if not s:
            continue
        if s.startswith(("*", "-", "\u2022")) or len(s) < 120:
            print("   " + s[:250])
