#!/usr/bin/env python3
"""Append pack batch 1 (runs/2026-09-23g) result lines to results.tsv and report sizes."""
import pathlib
from datetime import datetime, timezone

RUN = pathlib.Path("/home/ubuntu/Desktop/job-hunt/runs/2026-09-23g")
TSV = RUN / "results.tsv"
APPS = "/home/ubuntu/Desktop/job-hunt/applications"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ROWS = [
    (
        "deloitte-junior-data-engineer",
        "skipped",
        "dutch_gate SKIP_DUTCH_FLUENCY rc=10: posting requires uitstekende beheersing van de "
        "Nederlandse en Engelse taal, in woord en geschrift",
        "Hard skip 4(a), explicit Dutch plus English requirement (magnet.me lists Nederlands "
        "Vloeiend). External vacancy werkenbijdeloitte.nl/vacature/junior-data-engineer-ref3740b "
        "(Amsterdam). Fresh row (jt.py rows and row_gate both NO_ROW), no pack built under the "
        "skip rule. IND sponsor Deloitte Accountants B.V. on register line 2900. Salary not posted.",
        "none",
        f"{APPS}/deloitte-junior-data-engineer/jd.md",
        "https://werkenbijdeloitte.nl/vacature/junior-data-engineer-ref3740b/",
        "Deloitte own careers site (werkenbijdeloitte.nl), hard skip 4(a), nothing submitted",
        NOW,
    ),
    (
        "sogeti-medior-data-engineer",
        "skipped",
        "dutch_gate SKIP_DUTCH_FLUENCY rc=10: Because our assignments are fully conducted in Dutch, "
        "fluent Dutch language skills are a mandatory requirement for this role",
        "Hard skip 4(a), verbatim on the employer posting, which also asks Nederlands vloeiend op "
        "C1-niveau. External vacancy careers.capgemini.com job 1375215433 (ref 440839), remuneration "
        "budget to EUR 7.101,67 gross per month. Fresh row, no pack built under the skip rule. "
        "IND sponsor Sogeti Nederland B.V. on register line 10118.",
        "none",
        f"{APPS}/sogeti-medior-data-engineer/jd.md",
        "https://careers.capgemini.com/job/Groningen-Medior-Data-Engineer/1375215433/",
        "Capgemini/Sogeti careers (careers.capgemini.com), hard skip 4(a), nothing submitted",
        NOW,
    ),
    (
        "info-support-data-engineer",
        "queued",
        "Teamtailor form on werkenbij.infosupport.com job 5728947 accepted with cv.pdf and "
        "cover-letter.pdf attached, then the ATS required e-mail verification (Verifieer je "
        "e-mailadres, verification link sent to the candidate mailbox)",
        "Submission went through and is parked waiting for the one-time verification link: "
        "vishal-mail owns codes and nothing was fetched from the mailbox by this sweep. Form "
        "answers: Vishal Sehgal, vishalsehgal414@gmail.com, +31610159758, university question "
        "answered Jheronimus Academy of Data Science (JADS), motivation letter pasted (1423 chars), "
        "cv.pdf in the CV upload field and cover-letter.pdf under additional files. No CAPTCHA, one "
        "submission attempt, no retry needed. Salary startsalaris vanaf EUR 3.400 gross per month "
        "(40h): above the EUR 3.300 floor, below the 4k target, ask EUR 4.400-5.000. IND sponsor "
        "Info Support B.V. on register line 5515. Fallback address recruiter@infosupport.com "
        "(carriere.infosupport.com contact page) held in email-to-hr.md, not used.",
        f"{APPS}/info-support-data-engineer/cv.pdf,{APPS}/info-support-data-engineer/"
        f"cover-letter.pdf,{APPS}/info-support-data-engineer/cover-letter.md,"
        f"{APPS}/info-support-data-engineer/tailoring.json,{APPS}/info-support-data-engineer/"
        f"email-to-hr.md,{APPS}/info-support-data-engineer/fit.md",
        f"{APPS}/info-support-data-engineer/jd.md",
        "https://werkenbij.infosupport.com/jobs/5728947-data-engineer",
        "Info Support own careers site (Teamtailor apply form), submission accepted, awaiting e-mail "
        "verification",
        NOW,
    ),
    (
        "ventolines-medior-data-engineer",
        "skipped",
        "dutch_gate SKIP_DUTCH_LANGUAGE rc=11: posting is written in Dutch (27 Dutch markers, 4.7 per "
        "1k chars, 2 in the first 600)",
        "Gate heuristic, not a stated requirement: the JD itself asks for een goede beheersing van de "
        "Engelse taal with Dutch only bij voorkeur, salary is EUR 4.200-5.800 gross per month and the "
        "named contact Oana Etcu (oanaetcu@ventolines.nl) passes email_guard SEND_NAMED exit 0. No "
        "pack built and no contact made, so the parent can override this skip and re-queue the role "
        "at no cost. Fresh row, IND sponsor Ventolines B.V. on register line 12122.",
        "none",
        f"{APPS}/ventolines-medior-data-engineer/jd.md",
        "https://nl.linkedin.com/jobs/view/medior-data-engineer-at-ventolines-4470444039",
        "LinkedIn posting only, dutch_gate hard skip rc=11, nothing submitted",
        NOW,
    ),
]

before = TSV.stat().st_size if TSV.exists() else 0
with TSV.open("a", encoding="utf-8") as fh:
    for row in ROWS:
        fh.write("\t".join(row) + "\n")
print("appended", len(ROWS), "rows; bytes before", before, "after", TSV.stat().st_size)
print("tab-separated lines with 9 columns:")
for line in TSV.read_text(encoding="utf-8").splitlines():
    if not line.startswith("#") and line.strip():
        print(len(line.split("\t")), line.split("\t")[0], "|", line.split("\t")[1])
