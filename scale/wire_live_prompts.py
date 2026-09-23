#!/usr/bin/env python3
"""Wire the MODEL BUDGET instruction into the live sweep prompts, byte-for-byte elsewhere.

The gate, the API and the Settings dial can all be right while the feature does nothing, because a run's
volume is decided by the prompt (this is exactly what tests/test_prompt_drift_backoff.py exists for). This
edits ONLY the prompt string of each `*-job-hunt` job, through the JSON-escaped form, so nothing else in
the store changes, and writes a backup first.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import shutil
import sys

PROFILES = pathlib.Path("/home/ubuntu/.hermes/profiles")
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

ANCHOR = "a backoff is active; 0 means the full cap applies.\n"

BLOCK = """
- MODEL BUDGET (the money dial - ask it BEFORE discovery, then again before applying): this account has
  a daily model-spend budget and a sweep's volume is what it buys. Chain the two gates and use the second
  answer:
    python3 {ws}/gates/interview_backoff.py cap --plan-cap <the cap you would otherwise use>
    python3 {ws}/gates/model_budget.py ask --plan-cap <that cap>
  `ask` prints the cap THIS run may use and exit 0 means the budget is fine, 72 means the day's budget is
  spent and the cap was cut, and 70 means the subscriber set `budget.on_exceed: stop` - on exit 70 apply
  NOTHING this run (no applications, no new rows) and report why. Never work this arithmetic out yourself
  and never ignore the number the gate prints: it is the dial this account is paying for.
  `python3 {ws}/gates/model_budget.py line` prints the one sentence that accounts for a reduced volume -
  STATE that sentence verbatim in the run summary, because a sweep that quietly did less reads as the tool
  having broken.
- RECORD WHAT THE RUN COST, at the end of every sweep (it is what makes the budget above possible, and it
  costs no tokens):
    python3 {ws}/gates/model_budget.py record --job {job} --since <the ISO UTC time this run started>
  It reads this run's measured usage from the engine's own audit and appends one line (candidate, run id,
  tokens, model, cost) to this account's ledger at {ws}/data/usage.jsonl. Do it even when the run failed
  part-way, and put the dollar figure it prints in the run summary.
"""


def main(apply: bool) -> int:
    stores = sorted(PROFILES.glob("*/cron/jobs.json"))
    touched = 0
    for store in stores:
        raw = store.read_text(encoding="utf-8")
        doc = json.loads(raw)
        jobs = doc if isinstance(doc, list) else doc.get("jobs", [])
        changes = []
        for job in jobs:
            name = str(job.get("name") or "")
            prompt = job.get("prompt") or ""
            if not name.endswith("job-hunt") or not prompt or "MODEL BUDGET" in prompt:
                continue
            ws = f"/home/ubuntu/.hermes/profiles/{store.parent.parent.name}/workspace"
            block = BLOCK.format(ws=ws, job=name)
            if ANCHOR in prompt:
                new = prompt.replace(ANCHOR, ANCHOR + block, 1)
            elif "## REPORTING" in prompt:
                new = prompt.replace("## REPORTING", block.strip() + "\n\n## REPORTING", 1)
            else:
                new = prompt.rstrip("\n") + "\n" + block
            # the store is written with ensure_ascii=False (verified: the prompts carry non-ASCII and the
            # file holds no \u escapes), so the raw text is matched in that same encoding
            old_esc = json.dumps(prompt, ensure_ascii=False)[1:-1]
            new_esc = json.dumps(new, ensure_ascii=False)[1:-1]
            if raw.count(old_esc) != 1:
                print(f"  SKIP {name}: its prompt is not a unique string in {store}")
                continue
            raw = raw.replace(old_esc, new_esc)
            job["prompt"] = new
            changes.append(name)
        if not changes:
            continue
        check = json.loads(raw)
        after = check if isinstance(check, list) else check["jobs"]
        assert len(after) == len(jobs), "the store's job count changed"
        for before_job, after_job in zip(jobs, after):
            if before_job.get("name") in changes:
                assert "MODEL BUDGET" in after_job["prompt"]
                for needle in ("model_budget.py ask --plan-cap", "model_budget.py line",
                               "model_budget.py record --job", "STATE that sentence"):
                    assert needle in after_job["prompt"], (before_job["name"], needle)
            else:
                assert before_job.get("prompt") == after_job.get("prompt"), "an untouched prompt changed"
        print(f"  {store}: {len(raw)} bytes, wired {', '.join(changes)}"
              + ("" if apply else " (dry run)"))
        if apply:
            shutil.copy2(store, store.with_name(f"jobs.json.bak-budget-{STAMP}"))
            store.write_text(raw, encoding="utf-8")
            touched += 1
    if not touched and apply:
        print("  nothing to wire")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
