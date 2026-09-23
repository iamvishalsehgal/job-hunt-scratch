#!/usr/bin/env python3
"""Is FareHarbor gh_jid 8571117002 still on the Greenhouse board? (board list + embed endpoints)"""
import json, subprocess
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(url):
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code} %{size_download}",
                        "-A", UA, "--max-time", "30", url], capture_output=True, text=True, timeout=45)
    return r.stdout


def curlbody(url):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "30", url],
                          capture_output=True, text=True, timeout=45).stdout


for u in ["https://boards-api.greenhouse.io/v1/boards/fareharbor/jobs",
          "https://api.greenhouse.io/v1/boards/fareharbor/jobs",
          "https://boards.greenhouse.io/embed/job_app?for=fareharbor&token=8571117002",
          "https://job-boards.greenhouse.io/fareharbor/jobs/8571117002"]:
    print(u, "->", curl(u))

raw = curlbody("https://boards-api.greenhouse.io/v1/boards/fareharbor/jobs")
try:
    js = json.loads(raw)
    jobs = js.get("jobs", [])
    print("board jobs:", len(jobs))
    hit = [j for j in jobs if "8571117002" in str(j.get("id"))]
    print("target on board:", bool(hit))
    print("titles:", [j.get("title") for j in jobs][:15])
except Exception as e:
    print("board parse fail", e, raw[:200].replace("\n", " "))
