#!/usr/bin/env python3
"""Finalist audit: work-rights/salary/experience lines per JD + tracker grep for the company."""
import json
import os
import re

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
SCRATCH = "/home/ubuntu/job-hunt-scratch"
rows = json.load(open(os.path.join(SCRATCH, "eu_shortlist.json")))
FINALISTS = ["intact-insurance-ie", "euronext", "creditsafe-group", "version-1", "doit",
             "gea-group", "cityswift", "primer", "jpmorganchase", "workday", "mastercard",
             "block-labs", "musgrave", "fulcrum-digital", "sandbox-interactive"]
PAT = re.compile(r"authoris|authoriz|right to work|visa|permit|sponsor|immigration|"
                 r"salary|\u20ac|eur|per annum|per month|gross|years|must be eligible|"
                 r"legally|contractor|employment type", re.I)
TRK = open(os.path.join(WS, "build_tracker.py"), errors="replace").read().lower()
NAME_MAP = {"intact-insurance-ie": ["intact"], "euronext": ["euronext"], "creditsafe-group": ["creditsafe"],
            "version-1": ["version 1"], "doit": ["doit"], "gea-group": ["gea group"],
            "cityswift": ["cityswift"], "primer": ["primer"], "jpmorganchase": ["jpmorgan", "jpmc"],
            "workday": ["workday"], "mastercard": ["mastercard"], "block-labs": ["block labs"],
            "musgrave": ["musgrave"], "fulcrum-digital": ["fulcrum"], "sandbox-interactive": ["sandbox"]}
for r in rows:
    if r["company"] not in FINALISTS:
        continue
    txt = open(r["path"], errors="replace").read()
    body = txt.split("## Job description", 1)[-1]
    print("=" * 108)
    print("%s | %s (%d chars body)" % (r["company"], r["role"], len(body)))
    for name in NAME_MAP[r["company"]]:
        n = TRK.count(name)
        print("  TRACKER grep '%s': %d hits" % (name, n))
    for line in body.splitlines():
        s = re.sub(r"\s+", " ", line.replace("\u2022", "*")).strip()
        if 3 < len(s) < 330 and PAT.search(s):
            print("   * " + s)
