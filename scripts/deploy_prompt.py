#!/usr/bin/env python3
"""Swap one cron job's prompt on the VM, atomically, with a backup.

Usage: deploy_prompt.py <jobs.json> <job-name> <new-prompt-file>

Prints the old/new length, the section headings added and removed, and refuses to write when the new
prompt is missing a MUST-SURVIVE fact, so a bad port cannot reach the running job.
"""
import json
import pathlib
import shutil
import sys
import time

MUST_SURVIVE = (
    "Vishal Sehgal", "vishalsehgal414@gmail.com", "+31 6 10159758",
    "3 Dec 2026", "3,300", "4,400-5,000", "3,122", "4,357",
    "Van den Bosch", "IND recognised-sponsor", "Neo4j", "em-dash", "s-Hertogenbosch",
    "allow_reply", "--in-reply-to", "route_planner.py", "TRACKER HYGIENE", "ONE VACANCY IS ONE ROW",
)
REQUIRED_SECTIONS = (
    "## HARD GATES", "## ACCOUNT HANDLING AND VERIFICATION", "## ROUTE SELECTION",
    "## FIT PRIORITY", "## DEFERRALS AND INTERVIEW DEADLINES", "## REJECTION MEMORY",
    "## CRON-SAFE EXECUTION", "## SUB-AGENT DISCIPLINE", "## SCOPE AND COUNTRIES",
    "## VERIFICATION CODES", "## SCRATCH FILES", "## REPORTING", "## Workflow",
)
FORBIDDEN = ("(nhung: 4)", "[SKILL_PRUNED]", "/profiles/nhung", "manual exit 50 is allowed")


def headings(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith("## ")]


def main() -> int:
    jobs_path, job_name, prompt_path = (pathlib.Path(sys.argv[1]), sys.argv[2],
                                        pathlib.Path(sys.argv[3]))
    new_prompt = prompt_path.read_text(encoding="utf-8")
    missing = [f for f in MUST_SURVIVE if f not in new_prompt]
    if missing:
        print(f"REFUSED: the new prompt is missing {missing}")
        return 1
    stale = [f for f in FORBIDDEN if f in new_prompt]
    if stale:
        print(f"REFUSED: the new prompt still contains {stale}")
        return 1
    absent = [h for h in REQUIRED_SECTIONS if h not in new_prompt]
    if absent:
        print(f"REFUSED: the new prompt is missing sections {absent}")
        return 1
    if new_prompt.count("## VERIFICATION CODES") != 1:
        print(f"REFUSED: ## VERIFICATION CODES appears {new_prompt.count('## VERIFICATION CODES')} times")
        return 1
    data = json.loads(jobs_path.read_text(encoding="utf-8"))
    job = next((j for j in data["jobs"] if j.get("name") == job_name), None)
    if job is None:
        print(f"REFUSED: no job named {job_name} in {jobs_path}")
        return 1
    old = job.get("prompt") or ""
    backup = jobs_path.with_suffix(f".json.bak-promptport-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(jobs_path, backup)
    job["prompt"] = new_prompt
    tmp = jobs_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))          # the swap must not break the scheduler
    tmp.replace(jobs_path)
    old_h, new_h = headings(old), headings(new_prompt)
    added = [h for h in new_h if h not in old_h]
    removed = [h for h in old_h if h not in new_h]
    print(f"job      : {job_name} ({job['id']})")
    print(f"backup   : {backup}")
    print(f"length   : {len(old)} -> {len(new_prompt)} chars ({len(new_h)} sections)")
    print(f"added    : {len(added)}")
    for h in added:
        print(f"  + {h}")
    print(f"removed  : {len(removed)}")
    for h in removed:
        print(f"  - {h}")
    print(f"still there: {sum(1 for f in MUST_SURVIVE if f in new_prompt)}/{len(MUST_SURVIVE)} must-survive facts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
