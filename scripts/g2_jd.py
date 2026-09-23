#!/usr/bin/env python3
"""Fetch live JD text for the batch-1 (second wave) roles into their pack dirs."""
import json, pathlib, re, subprocess, html

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", url],
                       capture_output=True, text=True, timeout=60)
    return r.stdout


def totext(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>|</p>|</li>|</div>|</h[1-6]>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()


def workday(tenant, site, path, outdir, head):
    url = f"https://{tenant}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/{path}"
    d = json.loads(curl(url))
    jp = d.get("jobPostingInfo", {})
    body = totext(jp.get("jobDescription", ""))
    hdr = (f"# {jp.get('title')} - {jp.get('jobReqId')}\n"
           f"externalUrl: https://{tenant}.myworkdayjobs.com/{site}/{path}\n"
           f"postedOn: {jp.get('postedOn')} | startDate: {jp.get('startDate')} | canApply: {jp.get('canApply')}\n"
           f"location: {jp.get('location')} | additionalLocations: {jp.get('additionalLocations')}\n\n")
    (WS / "applications" / outdir).mkdir(parents=True, exist_ok=True)
    (WS / "applications" / outdir / "jd.md").write_text(head + hdr + body + "\n")
    print(outdir, "| title:", jp.get("title"), "| canApply:", jp.get("canApply"),
          "| posted:", jp.get("postedOn"), "| startDate:", jp.get("startDate"),
          "| len:", len(body))


# 1. Vanderlande
workday("vanderlande", "careers", "job/Veghel/Integration-Engineer_JR37386",
        "vanderlande-integration-engineer",
        "# Vanderlande Industries B.V. - Integration Engineer (JR37386), Veghel NL\n")

# 2. Medtronic refresh
try:
    workday("medtronic", "MedtronicCareers",
            "job/Heerlen-Limburg-Netherlands/Principal-Business-Performance-Analyst_R76374-1",
            "medtronic-principal-business-performance-analyst",
            "# Medtronic (KRK Medtronic BV) - Principal Business Performance Analyst (R76374), Heerlen NL\n")
except Exception as e:
    print("medtronic refresh failed:", e)

# 3. HCLTech SuccessFactors page
h = curl("https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/")
txt = totext(h)
out = APPS / "hcltech-ai-engineer"
out.mkdir(parents=True, exist_ok=True)
(out / "jd.md").write_text(
    "# HCLTech (HCL Technologies B.V.) - AI Engineer, Amsterdam NL\n"
    "externalUrl: https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/\n"
    "board: careers.hcltech.com (SAP SuccessFactors) | req 1367250555\n"
    "note: req now carries the title 'Senior Technical Lead'; the skill block is the AI/GenAI data-\n"
    "engineering role (log/metric pipelines, ML anomaly detection, GenAI in operational workflows).\n"
    "Liveness check 2026-09-23: page live, apply flow present.\n\n" + txt[:6000] + "\n")
print("hcltech-ai-engineer | len:", len(txt))
print("HCL apply markers:", [m for m in re.findall(r"(?i)(apply[^<\n]{0,40})", txt)][:8])

# 4. FareHarbor via Greenhouse API
g = curl("https://boards-api.greenhouse.io/v1/boards/fareharbor/jobs/8571117002?questions=false")
try:
    gj = json.loads(g)
    body = totext(gj.get("content", ""))
    outf = APPS / "fareharbor-lead-data-analytics"
    outf.mkdir(parents=True, exist_ok=True)
    (outf / "jd.md").write_text(
        f"# FareHarbor B.V. - {gj.get('title')}, Amsterdam NL\n"
        f"externalUrl: {gj.get('absolute_url')}\n"
        f"gh_jid: 8571117002 | location: {(gj.get('location') or {}).get('name')}\n"
        f"updated_at: {gj.get('updated_at')}\n\n" + body + "\n")
    print("fareharbor-lead-data-analytics | title:", gj.get("title"),
          "| loc:", (gj.get("location") or {}).get("name"), "| len:", len(body))
except Exception as e:
    print("greenhouse api failed:", e, g[:300])
