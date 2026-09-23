#!/usr/bin/env python3
"""Check return-contract line lengths and em-dash presence in produced materials."""
import json
import os

app = "/home/ubuntu/Desktop/job-hunt-nhung/applications/tronox-principal-data-governance"
evidence = ("ApplicantStack page after Submit: 'Application Received - Tronox' at /x/apply/a22jku1zoc30 (no captcha); "
            "board detail ID 40081739 NLD-Botlek live")
note = ("Board live on Tronox own board; dutch_gate OK (English JD), eu_scope OK NL, IND register lists Tronox Pigments "
        "(Holland) B.V.; screening answers honest (enterprise DG, SAP, catalogue = No); fit 3/5.")
files = ["nhung-2026-cv.pdf", "nhung-2026-cover-letter.pdf", "cover-letter.md", "cv-spec.json", "cv-payload.json",
         "nhung-2026-cv.html", "fit.md", "jd.md", "apply-url.txt", "email-to-hr.md"]
print("evidence len", len(evidence))
print("note len", len(note))
for f in files:
    p = os.path.join(app, f)
    txt = open(p, encoding="utf-8", errors="replace").read()
    print(f"{f} bytes={os.path.getsize(p)} emdash={txt.count(chr(0x2014))} endash={txt.count(chr(0x2013))}")
rt = "/home/ubuntu/Desktop/job-hunt-nhung/discovery/run-20260920b/nl/results.tsv"
print("results.tsv bytes", os.path.getsize(rt))
