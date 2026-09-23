#!/usr/bin/env python3
"""Append batch-3 results lines and report file sizes."""
import datetime
import os

BASE = "/home/ubuntu/Desktop/job-hunt/applications"
RES = "/home/ubuntu/Desktop/job-hunt/discovery/_sweep-2026-09-23f/results.tsv"

ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
print("now", ts)
print("--- existing tail ---")
with open(RES) as fh:
    lines = fh.read().splitlines()
print("rows:", len(lines))
for ln in lines[-3:]:
    print(ln[:200])

def p(slug, *names):
    return ",".join(os.path.join(BASE, slug, n) for n in names)

L = p("landal-greenparks-data-analyst", "cv.pdf", "cover-letter.pdf")
I = p("ifs-senior-software-engineer-ai-agents", "cv.pdf", "cover-letter.pdf")
F = p("funda-medior-backend-net-engineer", "cv.pdf", "cover-letter.pdf")
J = lambda s: os.path.join(BASE, s, "jd.md")

rows = [
    ["landal-greenparks-data-analyst", "submitted",
     "Workday roompot.wd103 submitted; congrats modal 'Thanks for applying'; Job_Application_ID=4b1189aac72f900e435598a76e430000",
     "Applied 2026-09-23 via portal (AUTO apply, no OTP needed); cv+cover uploaded step 2; source='Company Career Site' (tenant list has no LinkedIn); no portal account created - post-submit password step is vault-only",
     L, J("landal-greenparks-data-analyst"),
     "https://roompot.wd103.myworkdayjobs.com/Landal/job/Headoffice-Amsterdam/Data-Analyst_JR102999",
     "Workday portal (account gate not required)", ts],
    ["ifs-senior-software-engineer-ai-agents", "emailed",
     "SmartRecruiters one-click DataDome-walled; emailed privacy@ifs.com (guard pass, evidence: IFS recruitment privacy notice)",
     "One portal attempt only, no retry; no HR/careers mailbox published (ifs.com/careers asks for website applications); short body, cv.pdf + cover-letter.pdf attached",
     I, J("ifs-senior-software-engineer-ai-agents"),
     "https://jobs.smartrecruiters.com/IFS1/744000150119536-senior-software-engineer-ai-agents",
     "email fallback after walled portal", ts],
    ["funda-medior-backend-net-engineer", "blocked",
     "Recruitee form hCaptcha (captcha-base.recruiteecdn); no funda.nl address found on posting or contact pages",
     "BROWSER NEEDED: https://jobs.funda.nl/o/medior-backend-net-engineer/c/new?lang=en | contact hunt: posting, jobs.funda.nl privacy statement, funda.nl/contact, werkenbij.funda.nl - no mailbox; captcha not bypassed, one attempt only",
     F, J("funda-medior-backend-net-engineer"),
     "https://jobs.funda.nl/o/medior-backend-net-engineer/c/new?lang=en",
     "Recruitee (hCaptcha wall), no email route", ts],
    ["dustin-data-engineer", "skipped",
     "Posting states 'we dont provide any relocation or work permit sponsorship support' (own board, verified live 2026-09-23)",
     "HARD SKIP rule 4(b) no-visa-sponsor; IND register itself fine (Dustin Netherlands B.V. listed); no pack built, no portal attempt, no email spent",
     "", J("dustin-data-engineer"),
     "https://jobs.dustin.com/jobs/8102002-data-engineer",
     "own board (skipped before submission)", ts],
]

with open(RES, "a") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")
print("appended", len(rows))

print("--- wrote ---")
for slug, names in [("landal-greenparks-data-analyst",
                     ["jd.md", "tailoring.json", "cover-letter.md", "fit.md", "email-to-hr.md", "apply-url.txt", "cv.html", "cv.pdf", "cover-letter.pdf"]),
                    ("ifs-senior-software-engineer-ai-agents",
                     ["jd.md", "tailoring.json", "cover-letter.md", "fit.md", "email-to-hr.md", "cv.html", "cv.pdf", "cover-letter.pdf"]),
                    ("funda-medior-backend-net-engineer",
                     ["jd.md", "tailoring.json", "cover-letter.md", "fit.md", "email-to-hr.md", "cv.html", "cv.pdf", "cover-letter.pdf"])]:
    for n in names:
        fp = os.path.join(BASE, slug, n)
        if os.path.exists(fp):
            print(fp, os.path.getsize(fp))
print(RES, os.path.getsize(RES))
