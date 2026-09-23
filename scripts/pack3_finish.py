#!/usr/bin/env python3
"""Park the batch-3 skip packs in scratch and append the four results lines to the run TSV."""
import pathlib
import shutil
from datetime import datetime, timezone

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
RUN = WS / "runs" / "2026-09-23h"
SCRATCH = pathlib.Path.home() / "job-hunt-scratch" / "pack3-skipped"
SCRATCH.mkdir(parents=True, exist_ok=True)

for slug in ("ilionx-ai-engineer", "info-support-senior-data-engineer"):
    src = APPS / slug
    dst = SCRATCH / slug
    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = [
    ("ilionx-ai-engineer", "skipped",
     "own board lists 'Uitstekende beheersing van de Nederlandse taal, in woord en geschrift' - rule 4(a)",
     "Fit 4.0 technical, salary EUR 4.500-7.000, IlionX Group B.V. on IND register. The board form "
     "(Homerun) returned 'The URL you requested has been blocked' to the headless browser; per the hard "
     "rules no workaround and no retry. The Dutch-fluency clause settles it before any submission, so no "
     "form and no email were sent. Same clause skipped ilionx-data-analytics-engineer earlier.",
     "none",
     str(SCRATCH / "ilionx-ai-engineer" / "jd.md"),
     "https://nl.linkedin.com/jobs/view/ai-engineer-at-ilionx-4429349827",
     "skipped-dutch-fluency-rule-4a", now),
    ("farm-frites-business-intelligence-engineer", "skipped",
     "requires 'Uitstekende communicatieve vaardigheden in Nederlands en Engels' - rule 4(a)",
     "Fit 3.9 technical, salary EUR 4.725-6.938 clears the floor, Farm Frites International B.V. is on "
     "the IND register: the explicit Dutch plus English requirement is the only blocker. Needs 5 years as "
     "BI Engineer, which he does not hold as a dedicated title. No pack PDFs, no email.",
     "none",
     str(SCRATCH / "farm-frites-business-intelligence-engineer" / "jd.md"),
     "https://nl.linkedin.com/jobs/view/business-intelligence-engineer-at-farm-frites-4445741767",
     "skipped-dutch-fluency-rule-4a", now),
    ("momentum-agentic-ai-developer", "skipped",
     "gate exit 10 SKIP_DUTCH_FLUENCY on 'Vloeiend in het Nederlands, met uitstekende klantinteractie-'",
     "Fit 4.1 technical. Double blocker: fluent Dutch for a client-facing consultancy role, and no "
     "register entity for Momentum Digital Amsterdam (the only hit is Stichting GGZ Momentum, unrelated), "
     "so the employer is not a confirmed sponsor. Databricks Data Engineering and ML certifications are "
     "listed as a competency he must hold. No pack PDFs, no email.",
     "none",
     str(SCRATCH / "momentum-agentic-ai-developer" / "jd.md"),
     "https://nl.linkedin.com/jobs/view/agentic-ai-developer-at-momentum-4448535174",
     "skipped-dutch-language", now),
    ("info-support-senior-data-engineer", "skipped",
     "dutch_gate exit 11 SKIP_DUTCH_LANGUAGE on the own-board capture (46 Dutch markers, 5.42 per 1k)",
     "Fit 4.2, salary EUR 4.250-5.025, Info Support B.V. on the IND register (line 5515). The posting is "
     "written in Dutch throughout on carriere.infosupport.com and the LinkedIn mirror (both exit 11); it "
     "carries no explicit Dutch-fluency sentence, so this is the language-of-posting heuristic, not rule "
     "4(a). Pack built (jd, fit, tailoring, letter, mail draft), no PDFs rendered and nothing sent. The "
     "parent can re-queue this role if it wants a Dutch-language posting attempted.",
     "none",
     str(SCRATCH / "info-support-senior-data-engineer" / "jd.md"),
     "https://nl.linkedin.com/jobs/view/senior-data-engineer-at-info-support-4447008381",
     "skipped-dutch-language", now),
]

tsv = RUN / "results.tsv"
with tsv.open("a", encoding="utf-8") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")

print("appended", len(rows), "rows to", tsv)
print("--- files ---")
for p in sorted(SCRATCH.rglob("*")):
    if p.is_file():
        print(p, p.stat().st_size)
print("tsv now has", len(tsv.read_text().splitlines()), "lines")
