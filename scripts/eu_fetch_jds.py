#!/usr/bin/env python3
"""Fetch clean JD text for the shortlisted DE/IE postings via the LinkedIn guest
jobPosting API through the response cache. Saves markdown under
discovery/jd-eu-20260923/ and prints a per-id status line."""
import html
import json
import os
import re
import subprocess

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
JD_DIR = os.path.join(WS, "discovery", "jd-eu-20260923")
SCRATCH = "/home/ubuntu/job-hunt-scratch"
os.makedirs(JD_DIR, exist_ok=True)

SHORTLIST = [
    ("4468934803", "mastercard", "senior-data-engineer"),
    ("4468547268", "eir-business-talent", "data-engineer"),
    ("4467086651", "musgrave", "senior-data-engineer-data-platforms"),
    ("4469284073", "euronext", "data-engineer-for-ai"),
    ("4457787112", "workday", "data-engineer"),
    ("4466286298", "version-1", "data-engineer-microsoft-fabric"),
    ("4461744912", "creditsafe-group", "data-engineer-snowflake-databricks"),
    ("4468612043", "cityswift", "analytics-engineer"),
    ("4422815908", "block-labs", "data-platform-engineer"),
    ("4463975389", "doit", "data-engineer-cloud-saas-integrations"),
    ("4448185921", "gea-group", "industrial-data-engineer"),
    ("4455295221", "primer", "data-engineer-iii"),
    ("4464349772", "intact-insurance-ie", "data-engineer"),
    ("4461906199", "sandbox-interactive", "data-engineer"),
    ("4468366859", "rheindata", "data-engineer-microsoft-fabric"),
    ("4459689721", "jobspace", "azure-data-integration-engineer"),
    ("4405109763", "dymatrix", "junior-cloud-data-engineer-stuttgart"),
    ("4463523197", "dataciders", "junior-data-engineer"),
    ("4461183362", "neumann-kaffee-gruppe", "bi-data-engineer"),
    ("4429674225", "intersport-digital", "data-engineer-data-plattform"),
    ("4464552121", "aconext", "senior-data-engineer-data-platform"),
    ("4445716532", "montblanc", "analytics-engineer-finance"),
    ("4465020313", "infomotion", "snowflake-senior-data-engineer-frankfurt"),
    ("4466261340", "skeltech", "senior-data-engineering-azure-databricks"),
    ("4438816879", "jpmorganchase", "software-engineer-iii-databricks"),
    ("4462794465", "slalom", "data-engineer-munich"),
    ("4458714580", "eye-level-consulting", "senior-data-engineer-snowflake-databricks"),
    ("4467500362", "fulcrum-digital", "senior-data-engineer"),
]

TAG = re.compile(r"<[^>]+>")
MANY_NL = re.compile(r"\n{3,}")


def strip_html(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|li|div|h[1-6]|tr|ul|ol)>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "- ", h)
    h = TAG.sub("", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\xa0]+", " ", h)
    h = re.sub(r" *\n *", "\n", h)
    h = MANY_NL.sub("\n\n", h)
    return h.strip()


rows = []
for jid, company, role in SHORTLIST:
    url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/" + jid
    cp = subprocess.run(
        ["python3", os.path.join(WS, "tools/discovery_cache.py"), "fetch",
         "--url", url, "--candidate", "vishal"],
        capture_output=True, text=True, cwd=WS, timeout=120,
    )
    note = ""
    text = ""
    if cp.returncode != 0:
        note = "FETCH-FAILED rc=%d" % cp.returncode
    else:
        out = cp.stdout
        i = out.find("<!DOCTYPE")
        body = out[i:] if i >= 0 else out[out.find("<"):]
        # title / company / location from the posting header
        tm = re.search(r'class="[^"]*topcard__title[^"]*"[^>]*>(.*?)</h2>', body, re.S)
        cm = re.search(r'class="[^"]*topcard__org-name-link[^"]*"[^>]*>(.*?)</a>', body, re.S)
        lm = re.search(r'class="[^"]*topcard__flavor topcard__flavor--bullet[^"]*"[^>]*>(.*?)</span>', body, re.S)
        dm = re.search(r"topcard__flavor--metadata[^>]*>\s*([^<]*)", body)
        # criteria list holds Seniority / Employment type / Job function / Industries
        crit = re.findall(r'description__job-criteria-subheader">(.*?)</h3>\s*<span[^>]*>(.*?)</span>',
                          body, re.S)
        desc = re.search(r'class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', body, re.S)
        jd = strip_html(desc.group(1)) if desc else ""
        if not jd:
            note = "NO-DESCRIPTION-BLOCK"
        text = "\n".join([
            "# " + (strip_html(tm.group(1)) if tm else role),
            "company: " + (strip_html(cm.group(1)) if cm else company),
            "location: " + (strip_html(lm.group(1)) if lm else ""),
            "linkedin_id: " + jid,
            "linkedin_url: https://www.linkedin.com/jobs/view/" + jid,
            "posted_meta: " + (strip_html(dm.group(1)) if dm else ""),
            "criteria: " + " | ".join("%s=%s" % (a.strip(), strip_html(b))
                                      for a, b in crit),
            "",
            "## Job description",
            jd,
        ])
        path = os.path.join(JD_DIR, "%s-%s.md" % (company, role))
        with open(path, "w") as fh:
            fh.write(text)
    rows.append({"id": jid, "company": company, "role": role, "rc": cp.returncode,
                 "chars": len(text), "note": note, "path": path if text else ""})
    print("%s %-28s %-40s rc=%d chars=%d %s" % (jid, company, role, cp.returncode,
                                                len(text), note), flush=True)
ok = sum(1 for r in rows if r["rc"] == 0 and r["chars"] > 200)
print("CAPTURED %d/%d" % (ok, len(rows)))
json.dump(rows, open(os.path.join(SCRATCH, "eu_shortlist.json"), "w"), indent=1)
