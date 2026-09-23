#!/usr/bin/env python3
"""Show build_tracker.py context for the finalist name hits, so ATS-template hits
(Workday the ATS, etc.) can be told apart from real tracker rows."""
import os
import re

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
TXT = open(os.path.join(WS, "build_tracker.py"), errors="replace").read()
LINES = TXT.splitlines()
for name in ["musgrave", "euronext", "workday", "workday, inc", "creditsafe", "jpmorgan",
             "jpmc", "intact", "cityswift", "version 1", "doit", "gea group", "primer",
             "block labs", "sandbox"]:
    hits = [i for i, l in enumerate(LINES) if name in l.lower()]
    print("=" * 100)
    print("### %s -> %d line hits" % (name, len(hits)))
    for i in hits[:8]:
        s = re.sub(r"\s+", " ", LINES[i]).strip()
        print("  L%d: %s" % (i + 1, s[:220]))
