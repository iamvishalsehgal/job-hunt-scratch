#!/usr/bin/env python3
import json, subprocess, time
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
url = "https://vanderlande.wd3.myworkdayjobs.com/wday/cxs/vanderlande/careers/jobs"
for st in ["JR37386", "Integration Engineer", "Veghel"]:
    out = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", "-X", "POST",
                          "-H", "Content-Type: application/json", "-H", "Accept: application/json",
                          "--data-binary", json.dumps({"appliedFacets": {}, "limit": 50, "offset": 0,
                                                       "searchText": st}), url],
                         capture_output=True, text=True, timeout=60).stdout
    print("===", st, "rawlen", len(out))
    try:
        js = json.loads(out)
        print("  total:", js.get("total"))
        for p in js.get("jobPostings", [])[:10]:
            print("   ", p.get("title"), "|", p.get("externalPath"), "|", p.get("locationsText"))
    except Exception as e:
        print("  parse fail:", e, "|", out[:400].replace("\n", " "))
    time.sleep(2)
