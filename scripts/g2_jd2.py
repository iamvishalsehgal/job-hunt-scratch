#!/usr/bin/env python3
"""Write jd.md for hcltech-ai-engineer and fareharbor-lead-data-analytics."""
import json, pathlib, re, subprocess, html

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def curl(url):
    return subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "40", url],
                          capture_output=True, text=True, timeout=60).stdout


def totext(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>|</p>|</li>|</div>|</h[1-6]>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


# --- HCLTech (SuccessFactors) ---
h = curl("https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/")
t = totext(h)
d = APPS / "hcltech-ai-engineer"
d.mkdir(parents=True, exist_ok=True)
(d / "jd.md").write_text(
    "# HCLTech (HCL Technologies B.V.) - AI Engineer, Amsterdam NL\n"
    "externalUrl: https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/\n"
    "board: careers.hcltech.com (SAP SuccessFactors) | req 1367250555 | liveness check 2026-09-23\n"
    "title on board now: 'Senior Technical Lead'; skill block is the AI/GenAI data-engineering role\n\n" + t[:6000] + "\n")
print("HCL len", len(t), "| apply-links:", re.findall(r'(?i)href="([^"]*apply[^"]*)"', h)[:5])
print("HCL text markers:", t[:200].replace("\n", " "))

# --- FareHarbor via Greenhouse API ---
g = curl("https://boards-api.greenhouse.io/v1/boards/fareharbor/jobs/8571117002?questions=false")
try:
    gj = json.loads(g)
    body = totext(gj.get("content", ""))
    d = APPS / "fareharbor-lead-data-analytics"
    d.mkdir(parents=True, exist_ok=True)
    (d / "jd.md").write_text(
        f"# FareHarbor B.V. - {gj.get('title')}, Amsterdam NL\n"
        f"externalUrl: {gj.get('absolute_url')}\n"
        f"gh_jid: 8571117002 | location: {(gj.get('location') or {}).get('name')} | "
        f"updated_at: {gj.get('updated_at')}\n\n" + body + "\n")
    print("FH len", len(body), "| salary mention:", [s for s in re.findall(r"[^.]*salar[^.]*", body, re.I)][:3])
    print("FH dutch mention:", [s for s in re.findall(r"[^.]*[Dd]utch[^.]*", body)][:3])
except Exception as e:
    print("GH fail", e, g[:200])
