#!/usr/bin/env python3
"""Trim the IFS fallback email under the sender's 150-word prose cap."""
import re

p = "/home/ubuntu/Desktop/job-hunt/applications/ifs-senior-software-engineer-ai-agents/email-to-hr.md"

body = """# Fallback application email - SmartRecruiters one-click form is DataDome-walled (one attempt used, no retry)

# Evidence for the address: privacy@ifs.com is published on IFS's own recruitment privacy notice
# (https://www.ifs.com/privacy/ifs-recruitment), the page the job posting's Privacy Notice link points to.
# gates/email_guard.py --to privacy@ifs.com --evidence "<that page>" -> passes gates.
# No HR or careers mailbox is published: ifs.com/careers and the posting carry no address and ask candidates
# to apply through the website only.

Subject: Application: Senior Software Engineer, AI Agents - Vishal Sehgal

To: privacy@ifs.com

Dear IFS team,

I would like to apply for the Senior Software Engineer, AI Agents role in the Netherlands.

At Van den Bosch Transporten I built the org-wide AI service desk assistant (Copilot Studio with Power Automate
flows, around 220 tickets a week) over a 19,084-ticket knowledge base, with the retrieval layer underneath it: a
RAG and knowledge-graph pipeline with PII scrubbing, OCR and chunking. The flows update ticketing records and
route the work to a person when a rule says a human decides.

My current role is a fixed seven-month contract ending 3 December 2026, and my HSM permit needs an IND recognised
sponsor, which IFS Benelux B.V. is. I am available from 4 December 2026.

Attached: cv.pdf and cover-letter.pdf.

Kind regards,
Vishal Sehgal
vishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal
"""

with open(p, "w") as fh:
    fh.write(body)

txt = open(p).read()
prose = [ln for ln in txt.splitlines()
         if not re.match(r"^\s*(#|to:|cc:|subject|recipient|wants?|attachments?)\s*:", ln.strip(), re.I)]
count = len(" ".join(prose).split())
print("prose words:", count, "(cap 150)")
for w in ("automated", "automatic", "automatically", "automation", "auto-generated", "noreply", "do not reply"):
    hits = re.findall(r"[^.\n]*" + w + r"[^.\n]*", txt)
    if hits:
        print("HIT", w, hits)
