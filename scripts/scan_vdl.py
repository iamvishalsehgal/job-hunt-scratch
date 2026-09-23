#!/usr/bin/env python3
"""Print job postings from a Workday CXS /jobs JSON blob, filtered by location/term."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/job-hunt-scratch/vdl.json"
terms = [t.lower() for t in sys.argv[2:]] or ["integration"]
data = json.load(open(path, encoding="utf-8"))
print("total", data.get("total"))
for j in data.get("jobPostings", []):
    blob = (j.get("title", "") + " " + j.get("locationsText", "")).lower()
    if all(t in blob for t in terms) or any(t in blob for t in terms):
        print(j.get("title"), "|", j.get("locationsText"), "|", j.get("postedOn"), "|", j.get("externalPath"))
