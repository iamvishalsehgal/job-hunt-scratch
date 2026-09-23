#!/usr/bin/env python3
"""Vanderlande CXS search + HCL SuccessFactors + FareHarbor Greenhouse JD capture."""
import json, pathlib, re, subprocess, html

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(url, data=None):
    cmd = ["curl", "-sL", "-A", UA, "--max-time", "40", url]
    if data:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json",
                "-H", "Accept: application/json", "--data-binary", data]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout


def totext(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>|</p>|</li>|</div>|</h[1-6]>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


# --- Vanderlande: search the live careers site for the requisition ---
raw = curl("https://vanderlande.wd3.myworkdayjobs.com/wday/cxs/vanderlande/careers/jobs",
           json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0,
                       "searchText": "Integration Engineer"}))
try:
    js = json.loads(raw)
    print("VDL total:", js.get("total"), "results:")
    for p in js.get("jobPostings", []):
        print("   ", p.get("title"), "|", p.get("externalPath"), "|", p.get("locationsText"),
              "|", p.get("postedOn"), "|", p.get("bulletFields"))
except Exception as e:
    print("VDL search FAIL", e, raw[:300])
