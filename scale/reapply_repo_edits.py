#!/usr/bin/env python3
"""Re-apply the model-budget wiring to the two repo files ANOTHER session is also rewriting.

Evidence: provisioning/provision_tenant.py and engine/cron/jobs.template.json were both rewritten at
22:40:15 (one second, two files, sizes back to their pre-edit values) while this task's edits were already
in them - a concurrent agent in the same checkout. So the edits are applied here as an idempotent patch on
whatever the file currently says, rather than by pushing a whole file that could carry someone else's stale
copy over their work.

  python3 reapply_repo_edits.py --check      # report only
  python3 reapply_repo_edits.py              # apply, with a backup
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path("/home/ubuntu/jobhunt-agent")
HERE = pathlib.Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S")
GATE = "model_budget.py"

CALL_OLD = '''    sp = write_scope(cfg, ws) if not dry else ws / "eu_scope.json"
    print(f"  scope file: {sp}")'''
CALL_NEW = CALL_OLD + '\n    print(f"  {carry_budget_dial(cfg, ws, dry)}")'

TEMPLATE_ANCHOR = ("- LIFT the throttle automatically when no live interview remains: surface the deferred "
                   "rows first,\n  in fit order, under each candidate's own ping rule.\n\n"
                   "## REPORTING")
TEMPLATE_BLOCK = (
    "- MODEL BUDGET (the money dial - ask it BEFORE discovery, then again before applying): this account "
    "has\na daily model-spend budget and a sweep's volume is what it buys. Chain the two gates and use the "
    "second\nanswer:\n"
    "    python3 gates/interview_backoff.py cap --plan-cap <the cap you would otherwise use>\n"
    "    python3 gates/model_budget.py ask --plan-cap <that cap>\n"
    "  `ask` prints the cap THIS run may use. Exit 0 means the budget is fine, 72 means the day's budget is\n"
    "  spent and the cap was cut, and 70 means the subscriber set `budget.on_exceed: stop` - on exit 70 apply\n"
    "  NOTHING this run (no applications, no new rows) and report why. Never work this arithmetic out\n"
    "  yourself and never ignore the number the gate prints: it is the dial this account is paying for.\n"
    "  `python3 gates/model_budget.py line` prints the one sentence that accounts for a reduced volume -\n"
    "  STATE that sentence verbatim in the run summary, because a sweep that quietly did less reads as the\n"
    "  tool having broken.\n"
    "- RECORD WHAT THE RUN COST, at the end of every sweep (it is what makes the budget above possible, and\n"
    "  it costs no tokens):\n"
    "    python3 gates/model_budget.py record --job {{SLUG}}-job-hunt --since <the ISO UTC time this run "
    "started>\n"
    "  It reads this run's measured usage from the engine's own audit and appends one line (candidate, run\n"
    "  id, tokens, model, cost) to this account's ledger at {{WORKSPACE}}/data/usage.jsonl. Do it even when\n"
    "  the run failed part-way, and put the dollar figure it prints in the run summary.\n\n"
    "## REPORTING")


def reapply_provisioning(apply: bool) -> str:
    path = ROOT / "provisioning" / "provision_tenant.py"
    text = path.read_text(encoding="utf-8")
    if GATE in text and "carry_budget_dial" in text:
        return "provisioning: already wired"
    before = text
    if GATE not in text:
        old = 'GATE_FILES = ("eu_scope_gate.py", "effort_split.py", "dutch_gate.py", "row_gate.py",'
        if text.count(old) != 1:
            return "provisioning: REFUSED - GATE_FILES anchor not found (the other session changed it)"
        start = text.index(old)
        end = text.index(")", start) + 1
        block = text[start:end]
        if '"interview_backoff.py"' not in block:
            return f"provisioning: REFUSED - unexpected GATE_FILES: {block[:200]}"
        text = text[:start] + block[:-1].rstrip().rstrip(",") + f',\n              "{GATE}")' + text[end:]
    if "carry_budget_dial" not in text:
        anchor = "def write_scope(cfg: dict, ws: pathlib.Path) -> pathlib.Path:"
        if text.count(anchor) != 1:
            return "provisioning: REFUSED - write_scope anchor not found"
        snippet = (HERE / "carry_budget_snippet.py").read_text(encoding="utf-8")
        text = text.replace(anchor, snippet + anchor)
        if text.count(CALL_OLD) != 1:
            return "provisioning: REFUSED - the scope print anchor was not found"
        text = text.replace(CALL_OLD, CALL_NEW)
    compile(text, str(path), "exec")
    if apply and text != before:
        shutil.copy2(path, path.with_name(f"provision_tenant.py.bak-budget-{STAMP}"))
        path.write_text(text, encoding="utf-8")
    return "provisioning: wired" + ("" if apply else " (dry run)")


def reapply_template(apply: bool) -> str:
    path = ROOT / "engine" / "cron" / "jobs.template.json"
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    jobs = doc if isinstance(doc, list) else doc["jobs"]
    sweep = [j for j in jobs if str(j.get("name") or "").endswith("job-hunt")][0]
    if "MODEL BUDGET" in (sweep.get("prompt") or ""):
        return "template: already wired"
    left = json.dumps(TEMPLATE_ANCHOR, ensure_ascii=False)[1:-1]
    right = json.dumps(TEMPLATE_BLOCK, ensure_ascii=False)[1:-1]
    if raw.count(left) != 1:
        return f"template: REFUSED - anchor count {raw.count(left)}"
    out = raw.replace(left, right)
    check = json.loads(out)
    check = check if isinstance(check, list) else check["jobs"]
    wired = [j for j in check if "MODEL BUDGET" in (j.get("prompt") or "")]
    if len(wired) != 1 or wired[0]["name"] != "{{SLUG}}-job-hunt":
        return f"template: REFUSED - wired {[j.get('name') for j in wired]}"
    for needle in ("model_budget.py ask --plan-cap", "model_budget.py line",
                   "model_budget.py record --job", "STATE that sentence"):
        if needle not in wired[0]["prompt"]:
            return f"template: REFUSED - the prompt does not name {needle}"
    if len(check) != len(jobs):
        return "template: REFUSED - the store's job count changed"
    if apply:
        shutil.copy2(path, path.with_name(f"jobs.template.json.bak-budget-{STAMP}"))
        path.write_text(out, encoding="utf-8")
    return "template: wired" + ("" if apply else " (dry run)")


if __name__ == "__main__":
    apply = "--check" not in sys.argv
    print(reapply_provisioning(apply))
    print(reapply_template(apply))
