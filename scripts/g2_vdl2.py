#!/usr/bin/env python3
"""Probe Vanderlande JR37386 liveness."""
import json, subprocess
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def post(body):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", "-X", "POST",
                           "-H", "Content-Type: application/json", "-H", "Accept: application/json",
                           "--data-binary", json.dumps(body),
                           "https://vanderlande.wd3.myworkdayjobs.com/wday/cxs/vanderlande/careers/jobs"],
                          capture_output=True, text=True, timeout=60).stdout


def get(url):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", url],
                          capture_output=True, text=True, timeout=60).stdout


for st in ["JR37386", "Integration Engineer Veghel"]:
    js = json.loads(post({"appliedFacets": {}, "limit": 50, "offset": 0, "searchText": st}))
    print("== search:", st, "total:", js.get("total"))
    for p in js.get("jobPostings", [])[:8]:
        print("   ", p.get("title"), "|", p.get("externalPath"), "|", p.get("locationsText"), "|", p.get("postedOn"))

for path in ["job/Veghel/Integration-Engineer_JR37386",
             "job/Veghel/Integration-Engineer_JR37386-1"]:
    raw = get(f"https://vanderlande.wd3.myworkdayjobs.com/wday/cxs/vanderlande/careers/{path}")
    ok = '"jobPostingInfo"' in raw
    title = ""
    try:
        title = json.loads(raw).get("jobPostingInfo", {}).get("title", "")
    except Exception:
        pass
    print(path, "->", "JSON ok" if ok else "EMPTY/HTML", "| title:", title, "| bytes:", len(raw))
