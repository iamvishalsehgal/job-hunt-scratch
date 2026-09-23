#!/usr/bin/env python3
"""Append pack batch 3 results lines (2026-09-23g) to runs/2026-09-23g/results.tsv."""
import os, datetime

ROOT = "/home/ubuntu/.hermes/profiles/vishal/workspace"
APPS = ROOT + "/applications/"
TSV = ROOT + "/runs/2026-09-23g/results.tsv"
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ROLES = [
 ("dustin-data-engineer", "skipped",
  "own board and posting body: no relocation or work permit sponsorship for this specific job",
  "Hard skip rule 4(b). Dustin Netherlands B.V. on IND register, dutch_gate exit 0, band clears filters, posting refuses cover letters. No CV or letter spent.",
  "https://jobs.dustin.com/jobs/8102002-data-engineer",
  "skipped (own board, employer refuses permit support)"),
 ("ilionx-data-analytics-engineer", "skipped",
  "gates/dutch_gate.py exit 10 SKIP_DUTCH_FLUENCY; own board requires uitstekende beheersing van de Nederlandse taal",
  "Hard skip 4(a) Dutch fluency. EUR 4.500-6.500 clears the salary filter, IlionX Group B.V. on IND register. No portal attempt, no CV or letter, no email spent.",
  "https://werkenbij.ilionx.com/vacatures/data-analytics-engineer-5148924",
  "skipped (own careers board, explicit Dutch fluency required)"),
 ("athora-netherlands-azure-data-platform-engineer", "skipped",
  "gates/dutch_gate.py exit 10 SKIP_DUTCH_FLUENCY; posting requires Vloeiende beheersing van de Nederlandse taal",
  "Hard skip 4(a), same decision as run 2026-09-23a. Pay EUR 4,335-6,776 per month clears filters, Athora Netherlands N.V. on IND register. No CV or letter spent.",
  "https://nl.linkedin.com/jobs/view/azure-data-platform-engineer-at-athora-netherlands-4461667693",
  "skipped (own board, fluent Dutch required)"),
 ("cegeka-data-engineer-snowflake", "skipped",
  "gates/dutch_gate.py exit 11 SKIP_DUTCH_LANGUAGE, 14 Dutch markers 3.35 per 1k; own board 8276 is Dutch throughout",
  "Hard skip 4(a): Dutch-language posting, no English variant. Band around EUR 5.000-6.500 clears filters, Cegeka Nederland on IND register. No portal attempt, no CV or letter, no email spent.",
  "https://www.cegeka.com/nl-nl/werkenbij/vacatures/data-engineer-snowflake-8276",
  "skipped (own careers board, Dutch-language posting)"),
]

lines = []
for slug, outcome, evidence, note, apply_url, route in ROLES:
    folder = APPS + slug
    atts = ",".join(folder + "/" + n for n in ("jd.md", "fit.md", "apply-url.txt"))
    assert all(os.path.exists(a) for a in atts.split(",")), slug
    lines.append("\t".join([slug, outcome, evidence, note, atts,
                            folder + "/jd.md", apply_url, route, STAMP]))
    assert "|" not in evidence + note, slug
    assert len(evidence) <= 120, (slug, len(evidence))
    assert len(note) <= 200, (slug, len(note))

with open(TSV, "a") as fh:
    for line in lines:
        fh.write(line + "\n")

print("appended %d lines to %s (%d bytes)" % (len(lines), TSV, os.path.getsize(TSV)))
