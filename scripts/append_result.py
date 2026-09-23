#!/usr/bin/env python3
"""Append one tab-separated results line to a run results.tsv (fields sanitised)."""
import datetime
import json
import sys

path = "/home/ubuntu/Desktop/job-hunt-nhung/discovery/run-20260920b/nl/results.tsv"


def clean(s):
    return " ".join(str(s).replace("\t", " ").replace("\r", " ").replace("\n", " ").split())


fields = json.loads(sys.argv[1])
fields = [clean(f) for f in fields]
assert len(fields) == 9, len(fields)
line = "\t".join(fields) + "\n"
with open(path, "a", encoding="utf-8") as fh:
    fh.write(line)
print("APPENDED:", len(fields), "fields at", datetime.datetime.now(datetime.timezone.utc).isoformat())
print(line)
