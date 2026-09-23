#!/usr/bin/env python3
"""Append batch-1 (wave 2) results lines + fix the vanderlande evidence stub."""
import pathlib, subprocess
from datetime import datetime, timezone

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
RES = WS / "discovery" / "_sweep-2026-09-23f-g2" / "results.tsv"
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
A = "applications"

# vanderlande: replace the junk jd.md stub with the liveness evidence
(WS / A / "vanderlande-integration-engineer" / "jd.md").write_text(
    "# Vanderlande Integration Engineer (JR37386, Veghel) - VACANCY CLOSED (checked 2026-09-23)\n\n"
    "Own board check: https://vanderlande.wd3.myworkdayjobs.com/careers/job/Veghel/Integration-Engineer_JR37386\n"
    "- Workday CXS job endpoint returns an empty body (no jobPostingInfo) for JR37386 and JR37386-1\n"
    "- browser render of the same URL: 'The page you are looking for doesn't exist'\n"
    "- careers search for 'Integration Engineer' returns 54 jobs, none at Veghel under JR37386\n"
    "Outcome: hard skip (vacancy closed). No pack built, no CV/letter rendered.\n")

rows = [
    ["medtronic-principal-business-performance-analyst", "emailed",
     "tools/jt.py apply-email -> row 291 Emailed; to AskHR@medtronic.com; cv.pdf + cover-letter.pdf attached",
     "Workday portal needs a password at Create Account and browser_vault_save_login returned prompt_unavailable (headless), so the portal is a password wall; AskHR@medtronic.com listed in posting R76374 passed gates/email_guard.py exit 0",
     ",".join(str(WS / A / "medtronic-principal-business-performance-analyst" / f)
             for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")),
     str(WS / A / "medtronic-principal-business-performance-analyst" / "jd.md"),
     "https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers/job/Heerlen-Limburg-Netherlands/Principal-Business-Performance-Analyst_R76374-1",
     "email", now],
    ["hcltech-ai-engineer", "blocked",
     "Posting live on HCLTech's own board (req 1367250555, now titled Senior Technical Lead, AI/GenAI data-engineering skill block); pack + PDFs built",
     "BROWSER NEEDED: https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/ | contact hunt: no address anywhere on careers.hcltech.com or the job page; SAP SuccessFactors apply needs an account and its password cannot be created headlessly; hcl_recruitment@hcl.com is not an application route",
     ",".join(str(WS / A / "hcltech-ai-engineer" / f)
             for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")),
     str(WS / A / "hcltech-ai-engineer" / "jd.md"),
     "https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/",
     "portal:successfactors", now],
    ["fareharbor-lead-data-analytics", "blocked",
     "Live checked 2026-09-23: posting served only through FareHarbor's Greenhouse embed (job-boards.greenhouse.io/embed/job_app?for=fareharbor&token=8571117002); board API for gh_jid 8571117002 returns 404",
     "BROWSER NEEDED: https://fareharbor.com/careers/jobs/?gh_jid=8571117002 | contact hunt: no HR address on fareharbor.com/careers, /careers/jobs or the contact page; only support@fareharbor.com (customer support, not an application route). Greenhouse form is cross-origin + reCAPTCHA, so no first-contact email address qualified",
     "none",
     "none",
     "https://fareharbor.com/careers/jobs/?gh_jid=8571117002",
     "portal:greenhouse", now],
    ["vanderlande-integration-engineer", "skipped",
     "Vacancy closed on Vanderlande's own board: CXS job endpoint empty, browser render 'The page you are looking for doesn't exist', JR37386 absent from the live careers search",
     "Hard skip (rule 4d vacancy closed); no pack, no CV/letter rendered",
     "none",
     str(WS / A / "vanderlande-integration-engineer" / "jd.md"),
     "https://vanderlande.wd3.myworkdayjobs.com/careers/job/Veghel/Integration-Engineer_JR37386",
     "n/a", now],
]
with RES.open("a") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")
print("appended", len(rows), "rows to", RES)
print(RES.read_text()[-1200:])
