#!/usr/bin/env python3
"""Point the IFS fallback email at the evidence-bearing address and keep the body short."""
import os
import re

p = "/home/ubuntu/Desktop/job-hunt/applications/ifs-senior-software-engineer-ai-agents/email-to-hr.md"

body = """# Fallback application email - SmartRecruiters form is DataDome-walled (one attempt used, no retry)

Subject: Application: Senior Software Engineer, AI Agents - Vishal Sehgal

To: privacy@ifs.com
Evidence for that: published on IFS's own recruitment privacy notice at https://www.ifs.com/privacy/ifs-recruitment,
the page the job posting's own Privacy Notice link points to. gates/email_guard.py --to privacy@ifs.com --evidence
"IFS recruitment privacy notice ifs.com/privacy/ifs-recruitment" -> passes gates.
No HR/careers mailbox is published: ifs.com/careers and the posting carry no address and direct candidates to apply
through the website only.

Dear IFS team,

I would like to apply for the Senior Software Engineer, AI Agents role in the Netherlands.

At Van den Bosch Transporten I built the org-wide AI service desk assistant (Copilot Studio with Power Automate
flows, around 220 tickets a week) on a 19,084-ticket and 106K-document knowledge base, with the retrieval layer
underneath it: a RAG and knowledge-graph pipeline with PII scrubbing, OCR and chunking. The flows read and update
ticketing records and route the work to a person when a rule says a human decides.

My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Highly
Skilled Migrant permit runs to 3 December 2026, so IFS Benelux B.V. would be my IND recognised sponsor. I am
available from 4 December 2026.

Attached: cv.pdf and cover-letter.pdf.

Kind regards,
Vishal Sehgal
vishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal
"""

with open(p, "w") as fh:
    fh.write(body)

txt = open(p).read()
m = re.search(r"Dear IFS team,(.*?)Kind regards,", txt, re.S)
words = len(m.group(1).split()) if m else -1
print("body words:", words)
for w in ("automated", "automatic", "automatically", "automation", "auto-generated", "noreply", "do not reply"):
    hits = re.findall(r"[^.\n]*" + w + r"[^.\n]*", txt)
    if hits:
        print("HIT", w, hits)
print("ok", os.path.getsize(p))
