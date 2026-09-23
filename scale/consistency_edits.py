#!/usr/bin/env python3
"""Two consistency edits: the live tenant config carries the dial the gate enforces, and the prompt-drift
check asserts the budget wiring (so a later refactor cannot quietly drop the instruction the way the
interview backoff's prompt block was once dropped from the template).

  python3 consistency_edits.py [--check]
"""
from __future__ import annotations

import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path("/home/ubuntu/jobhunt-agent")
STAMP = time.strftime("%Y%m%d-%H%M%S")

BLOCK = """# ---------------------------------------------------------------- the spend dial
# The model layer's budget: what THIS ACCOUNT may spend on models in one UTC day, and what happens when
# that is reached. Measured, never estimated - every run appends its own measured usage to this account's
# ledger (<workspace>/data/usage.jsonl), and a sweep asks gates/model_budget.py before it spends anything.
# The Alerts view and the Cost panel both state the resulting sentence, so a slower hunt is never silent.
#
# This dial is WARN on purpose and sits just above this account's own measured burn (22 Sep 2026: ~$2.68/day
# against a $39/month plan, whose own cost basis is ~$0.40/day each). It therefore reports the gap between
# what the account pays and what it spends without changing what a sweep does; raise daily_usd to spend more,
# or set on_exceed to throttle/stop to bound it. A running account was measured at $2.68/day (vishal) and
# $2.75/day (nhung) on 22 Sep 2026, which is what these figures come from.
budget:
  daily_usd: 3.00
  on_exceed: warn         # warn = say so | throttle = apply at throttle_rate of the cap | stop = skip the run
  throttle_rate: 0.25

"""

LIVE_CONFIG = ROOT / "config" / "tenant.yaml"
PROMPT_BUDGET = ROOT / "engine" / "tools" / "prompt_budget.py"
MARKERS = ('    "- MODEL BUDGET",\n'
           '    "model_budget.py ask --plan-cap",\n'
           '    "model_budget.py record",\n')


def edit_live_config(apply: bool) -> str:
    text = LIVE_CONFIG.read_text(encoding="utf-8")
    if "\nbudget:\n" in text:
        return "live config: already carries the dial"
    anchor = "# ---------------------------------------------------------------- billing link\nbilling:"
    if text.count(anchor) != 1:
        return "live config: REFUSED - the billing anchor was not found"
    out = text.replace(anchor, BLOCK + anchor)
    if out.count("\nbudget:\n") != 1 or "\nbilling:\n" not in out:
        return "live config: REFUSED - the result would not parse as expected"
    if apply:
        shutil.copy2(LIVE_CONFIG, LIVE_CONFIG.with_name(f"tenant.yaml.bak-budget-{STAMP}"))
        LIVE_CONFIG.write_text(out, encoding="utf-8")
    return "live config: carries the dial" + ("" if apply else " (dry run)")


def edit_prompt_budget(apply: bool) -> str:
    if not PROMPT_BUDGET.is_file():
        return "prompt_budget.py: absent (not this task's file)"
    text = PROMPT_BUDGET.read_text(encoding="utf-8")
    if '"- MODEL BUDGET"' in text:
        return "prompt_budget.py: already asserts the budget markers"
    start = text.find("ASSERTED_IN_PROMPT = (")
    if start < 0:
        return "prompt_budget.py: REFUSED - ASSERTED_IN_PROMPT not found"
    end = text.index(")", start)
    out = text[:end] + MARKERS + text[end:]
    block = out[start:out.index(")", start)]
    if '"- INTERVIEW BACKOFF"' not in block:
        return "prompt_budget.py: REFUSED - the interview-backoff markers moved"
    for marker in ("- MODEL BUDGET", "model_budget.py ask --plan-cap", "model_budget.py record"):
        if marker not in block:
            return f"prompt_budget.py: REFUSED - {marker} did not land in the tuple"
    if apply:
        shutil.copy2(PROMPT_BUDGET, PROMPT_BUDGET.with_name(f"prompt_budget.py.bak-budget-{STAMP}"))
        PROMPT_BUDGET.write_text(out, encoding="utf-8")
    return "prompt_budget.py: asserts the budget markers" + ("" if apply else " (dry run)")


if __name__ == "__main__":
    apply = "--check" not in sys.argv
    print(edit_live_config(apply))
    print(edit_prompt_budget(apply))
