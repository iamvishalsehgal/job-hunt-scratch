#!/usr/bin/env python3
"""Build the dedupe set: tracker companies + companies already proposed in recent outputs."""
import glob
import json
import os
import re
import subprocess

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"

# 1. tracker companies via jt.py rows (authoritative)
cp = subprocess.run(["python3", os.path.join(WS, "tools/jt.py"), "rows"],
                    capture_output=True, text=True, cwd=WS)
tracker = []
for line in cp.stdout.splitlines():
    if "|" not in line:
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) >= 2 and parts[0].isdigit():
        tracker.append((parts[0], parts[1]))
print("TRACKER ROWS: %d" % len(tracker))
seen = set()
for n, c in tracker:
    key = c.lower()
    flag = " DUP" if key in seen else ""
    seen.add(key)
    print("  %s | %s%s" % (n, c, flag))

# 2. companies in outputs touched in the last 30h
SCRIPT = os.path.join(WS, "build_tracker.py")
print("\nbuild_tracker.py terms count:", len(re.findall(r"Data Engineer", open(SCRIPT, errors="replace").read())))

now = None
prop = {}
for f in glob.glob(os.path.join(WS, "runs", "*.json")) + \
         glob.glob(os.path.join(WS, "runs", "*", "*.json")) + \
         glob.glob(os.path.join(WS, "discovery", "*fresh*.json")) + \
         glob.glob(os.path.join(WS, "output", "**", "*.json"), recursive=True):
    try:
        st = os.stat(f)
    except OSError:
        continue
    if st.st_mtime < 1784000000:  # ~2026-07-... keep everything recent enough
        continue
    try:
        d = json.load(open(f))
    except Exception:
        continue
    rows = d if isinstance(d, list) else d.get("roles", [])
    if not isinstance(rows, list):
        continue
    for r in rows:
        if isinstance(r, dict) and r.get("company"):
            prop.setdefault(str(r["company"]).lower(), set()).add(os.path.relpath(f, WS))
print("\nCOMPANIES IN PRIOR OUTPUT FILES: %d" % len(prop))
for c in sorted(prop):
    print("  %s  <- %s" % (c, ", ".join(sorted(prop[c]))[:90]))
with open("/home/ubuntu/job-hunt-scratch/dedupe.json", "w") as fh:
    json.dump({"tracker": [c for _, c in tracker], "prior": sorted(prop)}, fh, indent=1)
