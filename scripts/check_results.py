#!/usr/bin/env python3
"""Validate the appended results line(s) in a run results.tsv."""
import os

path = "/home/ubuntu/Desktop/job-hunt-nhung/discovery/run-20260920b/nl/results.tsv"
cols = ["slug", "outcome", "evidence", "note", "attachments", "jd_path", "apply_url", "route", "finished_utc"]
raw = open(path, encoding="utf-8").read()
lines = [ln for ln in raw.split("\n") if ln.strip()]
bad = raw.count("\u2014") + raw.count("\u2013")
print("em/en dash count in results.tsv:", bad)
for ln in lines:
    if ln.startswith("#"):
        print("HEADER ok")
        continue
    parts = ln.split("\t")
    print("fields:", len(parts), "| expected", len(cols))
    for c, v in zip(cols, parts):
        print(f"  {c}: {v[:150]}")
    assert len(parts) == 9, "field count mismatch"
    assert parts[1] in {"submitted", "emailed", "blocked", "queued", "skipped", "interview", "offer", "rejected"}
    for chunk in parts[4].split(", "):
        p = chunk.split(" (")[0].strip()
        if p.startswith("/"):
            print("   exists:", os.path.exists(p), p, os.path.getsize(p) if os.path.exists(p) else "-")
print("OK")
