#!/usr/bin/env python3
"""Emit the return-contract JSON, with length checks."""
import json

ev = "'Application Received - Tronox' after Submit at /x/apply/a22jku1zoc30; detail ID 40081739 NLD-Botlek live"
note = ("Board live on Tronox own board; dutch_gate OK (English JD), eu_scope OK NL, IND register lists Tronox Pigments "
        "(Holland) B.V.; screening answers honest (enterprise DG, SAP, catalogue = No); fit 3/5.")
app = "/home/ubuntu/Desktop/job-hunt-nhung/applications/tronox-principal-data-governance"
att = (f"{app}/nhung-2026-cv.pdf, {app}/nhung-2026-cover-letter.pdf, {app}/cover-letter.md, {app}/cv-spec.json, "
       f"{app}/fit.md, {app}/jd.md")
role = f"ROLE tronox-principal-data-governance | submitted | {ev} | {note} | {att}"
assert len(ev) <= 120, len(ev)
assert len(note) <= 200, len(note)
assert "\u2014" not in role and "\u2013" not in role
out = {
  "first_line": "PACK 1 ROLES 1 DONE 1 FAILED 0",
  "role_lines": [role],
  "wrote_lines": [
    f"WROTE {app}/cv-spec.json 5373",
    f"WROTE {app}/cv-payload.json 9044",
    f"WROTE {app}/nhung-2026-cv.html 29180",
    f"WROTE {app}/nhung-2026-cv.pdf 66349",
    f"WROTE {app}/cover-letter.md 2666",
    f"WROTE {app}/nhung-2026-cover-letter.pdf 19325",
    f"WROTE {app}/fit.md 2470",
    f"WROTE {app}/jd.md 7289",
    f"WROTE {app}/apply-url.txt 55",
    f"WROTE {app}/email-to-hr.md 882 (NOT sent: email is read-only)",
    "WROTE /home/ubuntu/Desktop/job-hunt-nhung/discovery/run-20260920b/nl/results.tsv 3041"
  ],
  "summary": "END"
}
print("ev len", len(ev), "note len", len(note))
print(json.dumps(out, ensure_ascii=False, indent=1))
