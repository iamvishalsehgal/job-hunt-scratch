#!/usr/bin/env python3
"""Print company/role/location/country of every roles-*.json under runs/ + discovery/."""
import glob
import json
import os

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
pats = [os.path.join(WS, "runs", "*.json"), os.path.join(WS, "discovery", "*.json"),
        os.path.join(WS, "output", "*.json")]
for p in pats:
    for f in sorted(glob.glob(p)):
        try:
            d = json.load(open(f))
        except Exception as e:  # noqa: BLE001
            continue
        rows = d if isinstance(d, list) else d.get("roles", [])
        if not isinstance(rows, list):
            continue
        out = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            if not (r.get("company") and r.get("role")):
                continue
            out.append("%s | %s | %s | %s" % (r.get("company"), r.get("role"),
                                              r.get("location"), r.get("country")))
        if out:
            print("=== " + os.path.relpath(f, WS) + " (%d)" % len(out))
            for line in out:
                print("   " + line)
