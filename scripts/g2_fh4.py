#!/usr/bin/env python3
"""Find FareHarbor's greenhouse board token + whether gh_jid 8571117002 is live."""
import re, subprocess
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(u):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "30", u],
                          capture_output=True, text=True, timeout=45).stdout


h = curl("https://fareharbor.com/careers/jobs/?gh_jid=8571117002")
print("careers page len:", len(h))
print("board tokens:", sorted(set(re.findall(r'(?i)(?:greenhouse\.io/|for["\']?\s*[:=]\s*["\']?)([a-z0-9_-]{3,30})', h)))[:20])
print("gh_jid refs:", sorted(set(re.findall(r"gh_jid[=:\"'\s]+(\d+)", h)))[:10])
print("title in page:", re.findall(r"(?i)<title>(.{0,90})", h)[:2])
print("has Lead, Data Analytics:", "Lead, Data Analytics" in h, "| has Published:", "Published" in h)
for tok in ["fareharbor", "fareharborjobs", "fareharborcareers"]:
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}", "-A", UA, "--max-time",
                        "25", f"https://boards-api.greenhouse.io/v1/boards/{tok}/jobs/8571117002"],
                       capture_output=True, text=True, timeout=40).stdout
    print("token", tok, "->", r)
