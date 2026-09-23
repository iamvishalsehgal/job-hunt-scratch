#!/usr/bin/env python3
"""Verify the batch-3 handoff: 4 rows in the run TSV, each with 9 fields, and the parked packs intact."""
import pathlib

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
RUN = WS / "runs" / "2026-09-23h"
SCRATCH = pathlib.Path.home() / "job-hunt-scratch" / "pack3-skipped"
MINE = ("ilionx-ai-engineer", "farm-frites-business-intelligence-engineer",
        "momentum-agentic-ai-developer", "info-support-senior-data-engineer")

lines = [l for l in (RUN / "results.tsv").read_text().splitlines() if l and not l.startswith("#")]
print("total result rows:", len(lines))
seen = []
for l in lines:
    f = l.split("\t")
    if f[0] in MINE:
        seen.append(f[0])
        print(f"{f[0]} | fields={len(f)} | outcome={f[1]} | utc={f[-1]} | jd_exists={pathlib.Path(f[5]).exists()}")
print("batch-3 rows found:", len(seen), "in order:", seen == list(MINE))
print("packs parked:", all((SCRATCH / s).is_dir() for s in MINE))
print("left in applications/:", [s for s in MINE if (WS / 'applications' / s).exists()])
print("ilionx fit.md corrected:", "Uitstekende beheersing" in (SCRATCH / "ilionx-ai-engineer" / "fit.md").read_text())
print("ilionx docs:", [(p.name, p.stat().st_size) for p in sorted((SCRATCH / "ilionx-ai-engineer").iterdir())])
