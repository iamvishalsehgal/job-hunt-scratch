#!/usr/bin/env python3
"""Validate the written roles file against the required key set + note contents."""
import json
import os
import re

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
P = os.path.join(WS, "discovery", "eu_fresh_20260923b.json")
d = json.load(open(P))
REQ = ["slug", "company", "role", "location", "country", "fit", "apply_url", "kw", "jd_path",
       "notes"]
print("rows:", len(d), "keys ok:", all(list(r.keys()) == REQ for r in d))
for r in d:
    notes = r["notes"]
    gate = re.search(r"gate exit \d+ -> '[^']{20,120}", notes)
    print("-" * 100)
    print("%s | %s | %s | %s | fit %s" % (r["company"], r["role"], r["location"], r["country"],
                                          r["fit"]))
    print("   kw: %s" % r["kw"])
    print("   url: %s" % r["apply_url"])
    print("   jd: %s (%d bytes)" % (r["jd_path"], os.path.getsize(os.path.join(WS, r["jd_path"]))))
    print("   gate line: %s" % (gate.group(0) if gate else "*** MISSING ***"))
    print("   notes bytes: %d" % len(notes))
    for must in ["sponsor: not stated", "EUR 3,300/month", "FRESHNESS", "GAPS TO DISCLOSE",
                 "Tracker check"]:
        if must not in notes:
            print("   *** note missing token: %s" % must)
