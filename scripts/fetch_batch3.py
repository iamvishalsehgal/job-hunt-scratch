#!/usr/bin/env python3
"""Capture JDs for pack batch 3 (2026-09-23g) and run the Dutch gate on each."""
import subprocess, re, html as h, os, datetime, json

ROOT = "/home/ubuntu/.hermes/profiles/vishal/workspace"
APPS = os.path.join(ROOT, "applications")

ROLES = [
    dict(slug="dustin-data-engineer", jid="4459351316", company="Dustin",
         role="Data Engineer", location="Arnhem",
         apply="https://nl.linkedin.com/jobs/view/data-engineer-at-dustin-4459351316",
         own="https://jobs.dustin.com/jobs/8102002-data-engineer",
         own_note="Please note that for this specific job, we dont provide any relocation or work permit sponsorship support. (own board, verified 2026-09-23)"),
    dict(slug="ilionx-data-analytics-engineer", jid="4469894891", company="ilionx",
         role="Data Analytics Engineer", location="Zwolle",
         apply="https://nl.linkedin.com/jobs/view/data-analytics-engineer-at-ilionx-4469894891",
         own="https://werkenbij.ilionx.com/vacatures/data-analytics-engineer-5148924",
         own_note="Je hebt een uitstekende beheersing van de Nederlandse taal in woord en geschrift. (own board, verified 2026-09-23)"),
    dict(slug="athora-netherlands-azure-data-platform-engineer", jid="4461667693",
         company="Athora Netherlands", role="Azure Data Platform Engineer", location="Amsterdam",
         apply="https://nl.linkedin.com/jobs/view/azure-data-platform-engineer-at-athora-netherlands-4461667693",
         own="https://athora.recruitee.com (Athora own Recruitee board)",
         own_note="Vloeiende beheersing van de Nederlandse taal (fluent Dutch required). Posting body is Dutch throughout; pay range EUR 4,335-6,776/mo is stated on the LinkedIn card. (verified 2026-09-23)"),
    dict(slug="cegeka-data-engineer-snowflake", jid="4458898351", company="Cegeka",
         role="Data Engineer - Snowflake", location="Veenendaal",
         apply="https://nl.linkedin.com/jobs/view/data-engineer-snowflake-at-cegeka-4458898351",
         own="https://www.cegeka.com/nl-nl/werkenbij/vacatures/data-engineer-snowflake-8276",
         own_note="Entire own-board posting (8276) is written in Dutch, no English variant. (verified 2026-09-23)"),
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def fetch(url):
    try:
        out = subprocess.run(["curl", "-s", "-L", "-A", UA, "--max-time", "30", url],
                             capture_output=True, text=True, timeout=45)
        return out.stdout
    except Exception as e:
        return ""


def desc_from(html_text):
    m = re.search(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>\s*</div>', html_text, re.S)
    if not m:
        m = re.search(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*)', html_text, re.S)
    if not m:
        return ""
    txt = re.sub(r"<(br|/li|/p|/ul|/div)[^>]*>", "\n", m.group(1))
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = h.unescape(txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
report = []
for r in ROLES:
    folder = os.path.join(APPS, r["slug"])
    os.makedirs(folder, exist_ok=True)
    body = ""
    for attempt in (1, 2):
        raw = fetch("https://www.linkedin.com/jobs-guest/jobs/view/%s" % r["jid"])
        body = desc_from(raw)
        if len(body) > 300:
            break
    header = [
        "# JD capture - %s, %s (%s)" % (r["company"], r["role"], r["location"]),
        "",
        "- source (LinkedIn posting): %s" % r["apply"],
        "- employer own board: %s" % r["own"],
        "- captured UTC: %s" % stamp,
        "",
        "## Employer own-board requirement line (decisive)",
        "%s" % r["own_note"],
        "",
        "## Captured posting text",
        body if body else "(LinkedIn guest view returned no description markup; see the employer own board above.)",
        "",
    ]
    with open(os.path.join(folder, "jd.md"), "w") as fh:
        fh.write("\n".join(header))
    gate = subprocess.run(["python3", os.path.join(ROOT, "gates", "dutch_gate.py"),
                           os.path.join(folder, "jd.md")],
                          capture_output=True, text=True, cwd=ROOT)
    report.append(dict(slug=r["slug"], chars=len(body), rc=gate.returncode,
                       gate_out=(gate.stdout + gate.stderr).strip()[-300:]))

print(json.dumps(report, indent=1))
