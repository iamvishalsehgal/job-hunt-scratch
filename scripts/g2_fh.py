#!/usr/bin/env python3
"""Debug greenhouse API for FareHarbor + capture JD body."""
import json, pathlib, re, subprocess, html

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(url):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", url],
                          capture_output=True, text=True, timeout=60).stdout


raw = curl("https://boards-api.greenhouse.io/v1/boards/fareharbor/jobs/8571117002")
print("rawlen", len(raw), "| head:", raw[:300].replace("\n", " "))
try:
    gj = json.loads(raw)
    print("keys:", list(gj.keys()))
    for k in ("title", "absolute_url", "updated_at", "location"):
        print("  ", k, "=", gj.get(k))
    print("  content len:", len(gj.get("content") or ""))
except Exception as e:
    print("parse fail", e)
