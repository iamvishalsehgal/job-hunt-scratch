#!/usr/bin/env python3
"""CXS JD fetch by full host."""
import json, pathlib, re, subprocess, html, sys

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
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
    return re.sub(r"\n\s*\n+", "\n", h).strip()


for host, tenant, site, path, slug, head in [
    ("vanderlande.wd3.myworkdayjobs.com", "vanderlande", "careers",
     "job/Veghel/Integration-Engineer_JR37386", "vanderlande-integration-engineer",
     "# Vanderlande Industries B.V. - Integration Engineer (JR37386), Veghel NL\n"),
    ("medtronic.wd1.myworkdayjobs.com", "medtronic", "MedtronicCareers",
     "job/Heerlen-Limburg-Netherlands/Principal-Business-Performance-Analyst_R76374-1",
     "medtronic-principal-business-performance-analyst",
     "# Medtronic (KRK Medtronic BV) - Principal Business Performance Analyst (R76374), Heerlen NL\n"),
]:
    url = f"https://{host}/wday/cxs/{tenant}/{site}/{path}"
    raw = curl(url)
    try:
        jp = json.loads(raw).get("jobPostingInfo", {})
    except Exception as e:
        print(slug, "FAIL", e, raw[:200].replace("\n", " "))
        continue
    body = totext(jp.get("jobDescription", ""))
    d = WS / "applications" / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "jd.md").write_text(
        head + f"externalUrl: https://{host}/{site}/{path}\n"
        f"postedOn: {jp.get('postedOn')} | startDate: {jp.get('startDate')} | canApply: {jp.get('canApply')}\n"
        f"location: {jp.get('location')} | addl: {jp.get('additionalLocations')}\n"
        f"timeType: {jp.get('timeType')}\n\n" + body + "\n")
    print(slug, "| canApply:", jp.get("canApply"), "| posted:", jp.get("postedOn"),
          "| start:", jp.get("startDate"), "| endDate:", jp.get("endDate"),
          "| len:", len(body), "| title:", jp.get("title"))
