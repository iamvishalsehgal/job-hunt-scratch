#!/usr/bin/env python3
"""What a sweep prompt costs, and whether the rules are all still reachable.

The prompt is re-sent on every API call, so its size is multiplied by the calls in a sweep and by the
sweeps in a day. This reports that multiplication, and it refuses to let a rule go missing while the
prompt shrinks:

  * MUST_SURVIVE - a rule marker the prompt carried BEFORE the move has to be reachable AFTER it,
    either still in the prompt or in one of the playbook files the prompt names. Only markers that
    the pre-change prompt actually carried are enforced, so a tenant that never had a rule is not
    asked to gain one.
  * ASSERTED_IN_PROMPT - other tooling reads the LIVE PROMPT for these strings, so they may not move
    into a file at all.

Every number printed here is either read off the store or divided by CHARS_PER_TOKEN, which is
MEASURED (see the anchors in the constant's comment) rather than assumed.

  python3 engine/tools/prompt_budget.py                  # every sweep store on this host
  python3 engine/tools/prompt_budget.py --template
  python3 engine/tools/prompt_budget.py --json
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import prompt_playbook as pp  # noqa: E402

# Measured, not assumed. Prompt chars and first-call input tokens, read from the agent logs on two
# sessions whose prompt sizes are far apart and whose base context is otherwise the same:
#   vishal 2026-09-21 23:36  36,725 chars / 25,776 in  ->  2026-09-22 22:00  67,878 chars / 33,192 in
#          (67,878 - 36,725) / (33,192 - 25,776) = 4.20 chars per token
#   nhung  2026-09-21 21:28  50,790 chars / 24,614 in  ->  2026-09-22 22:00  63,440 chars / 27,893 in
#          (63,440 - 50,790) / (27,893 - 24,614) = 3.86 chars per token
# Mean 4.03. That is what makes 69,772 chars ~= 17.3k tokens, matching the ~1M prompt input tokens per
# sweep the logs showed. The numbers are recomputable from the logs; see
# ~/job-hunt-scratch/scale/cost-analysis.md.
CHARS_PER_TOKEN = 4.03

# Refuse to let a rule vanish. Checked against the prompt UNION every playbook it names, but only for
# markers the pre-change prompt itself carried.
MUST_SURVIVE = (
    "EU ONLY, NO EXCEPTIONS",
    "TIER 2 is a ROTATION POOL",
    "never widen the keyword list",
    "exits 70 when",
    "exit 71 means NL has fallen below 80%",
    "eu_scope_gate.py validate",
    "eu_scope_gate.py country --location",
    "eu_scope_gate.py manual",
    "PUT THIS RULE IN EVERY DISCOVERY SUB-AGENT BRIEF VERBATIM",
    "effort_split.py check --nl",
    "effort_split.py discovery",
    "effort_split.py status",
    "At most TWO addresses per company per sweep",
    "recruitment@ / careers@ / jobs@",
    "otp_fetch.py",
    "IND recognised-sponsor register",
    "highly-skilled-migrant permit",
    "never filled with an invention",
    "GOOGLE SHEET IS THE TRACKER",
    "Greenhouse, Ashby, Lever",
    "HARD SKIP, record it",
    "unexplained entry",
)

# Other tooling reads the LIVE PROMPT for these, so they may not move into a file.
ASSERTED_IN_PROMPT = (
    "## WHEN THE AUTOMATIC APPLY FAILS",
    "- INTERVIEW BACKOFF",
    "interview_backoff.py cap",
    "interview_backoff.py line",
    "STATE the sentence",
    "- MODEL BUDGET",
    "model_budget.py ask --plan-cap",
    "model_budget.py record",
)

# Measured on this host: calls per sweep (median over the logged sweep sessions) and the sweeps a day
# the cron store really fires (counted from cron/executions.db, not from the interval on the schedule).
CALLS_PER_SWEEP = 58      # median over every logged sweep session (vishal 54, nhung 96)
SWEEPS_PER_DAY = 9        # both stores fired 9 sweeps on 2026-09-22 (cron/executions.db), not 144


def backup_prompt(store: pathlib.Path):
    """The pre-change prompt, when a backup from the move is still on disk."""
    baks = sorted(glob.glob(str(store) + ".bak-playbook-*"))
    if not baks:
        return None
    try:
        d = json.loads(pathlib.Path(baks[-1]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for j in (d["jobs"] if isinstance(d, dict) else d):
        if str(j.get("name") or "").endswith(pp.SUFFIX):
            return j.get("prompt") or ""
    return None


def reachable_text(prompt: str, refs_dir: pathlib.Path) -> str:
    text = prompt
    if refs_dir.is_dir():
        for f in sorted(refs_dir.glob("*.md")):
            text += "\n" + f.read_text(encoding="utf-8")
    return text


def measure(name: str, prompt: str, refs_dir: pathlib.Path, before: str = None) -> dict:
    ws_token = str(refs_dir.parent)
    _, parts = pp.split(before if before else prompt, ws_token)
    moved = sorted(parts)
    reach = reachable_text(prompt, refs_dir)
    on_disk = 0
    missing_files = []
    for n in moved:
        f = refs_dir / n
        if f.is_file():
            on_disk += len(f.read_text(encoding="utf-8"))
        else:
            missing_files.append(str(f))
    out = {
        "name": name,
        "chars": len(prompt),
        "chars_before": len(before) if before else None,
        "tokens_per_call": round(len(prompt) / CHARS_PER_TOKEN),
        "sections_inline": len(pp.sections(prompt)),
        "sections_moved": sum(len(v) for v in parts.values()),
        "playbook_chars": on_disk,
        "playbook_files": moved,
        "missing_files": missing_files,
        # scoped to the pre-change prompt: a tenant that never carried a rule is not asked to gain one,
        # and a rule the prompt did carry may not become unreachable.
        "missing_must_survive": [m for m in MUST_SURVIVE if before and m in before and m not in reach],
        "missing_asserted_in_prompt": [m for m in ASSERTED_IN_PROMPT if before and m in before and m not in prompt],
    }
    if before:
        saved = len(before) - len(prompt)
        out.update({
            "chars_saved": saved,
            "tokens_saved_per_call": round(saved / CHARS_PER_TOKEN),
            "tokens_saved_per_sweep": round(saved / CHARS_PER_TOKEN * CALLS_PER_SWEEP),
            "tokens_saved_per_day": round(saved / CHARS_PER_TOKEN * CALLS_PER_SWEEP * SWEEPS_PER_DAY),
        })
    return out


def show(r: dict) -> None:
    print("%s" % r["name"])
    print("  prompt chars            : %d%s" % (
        r["chars"],
        " (was %d, -%d, -%.1f%%)" % (r["chars_before"], r["chars_before"] - r["chars"],
                                     100.0 * (r["chars_before"] - r["chars"]) / r["chars_before"])
        if r["chars_before"] else ""))
    print("  prompt tokens / call    : %d   (chars / %.2f, measured)" % (r["tokens_per_call"], CHARS_PER_TOKEN))
    print("  sections inline         : %d" % r["sections_inline"])
    print("  sections in playbooks   : %d  -> %s" % (r["sections_moved"], ", ".join(r["playbook_files"]) or "none"))
    print("  playbook bytes on disk  : %d" % r["playbook_chars"])
    if r.get("tokens_saved_per_call") is not None:
        print("  tokens saved / call     : %d" % r["tokens_saved_per_call"])
        print("  tokens saved / sweep    : %d   (x %d calls, measured median)" % (
            r["tokens_saved_per_sweep"], CALLS_PER_SWEEP))
        print("  tokens saved / day      : %d   (x %d sweeps, counted from executions.db)" % (
            r["tokens_saved_per_day"], SWEEPS_PER_DAY))
    print("  must-survive markers    : %d missing%s" % (
        len(r["missing_must_survive"]), "" if not r["missing_must_survive"] else "  -> %s" % r["missing_must_survive"]))
    print("  asserted-in-prompt      : %d missing%s" % (
        len(r["missing_asserted_in_prompt"]),
        "" if not r["missing_asserted_in_prompt"] else "  -> %s" % r["missing_asserted_in_prompt"]))


def targets(a) -> list:
    if a.template:
        return [(pp.TEMPLATE, pp.REFERENCES)]
    if a.jobs:
        s = pathlib.Path(a.jobs)
        return [(s, s.parent.parent / "workspace" / "references")]
    return [(s, s.parent.parent / "workspace" / "references") for s in pp.stores()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="")
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows, bad = [], []
    for store, refs in targets(a):
        name, prompt = pp.sweep_prompt(store)
        if prompt is None:
            continue
        r = measure(name, prompt, refs, backup_prompt(store))
        rows.append(r)
        bad += ["%s: a pointer names a file that is not there: %s" % (name, f) for f in r["missing_files"]]
        bad += ["%s: a rule the prompt carried is no longer reachable: %s" % (name, m)
                for m in r["missing_must_survive"]]
        bad += ["%s: this may no longer leave the prompt: %s" % (name, m)
                for m in r["missing_asserted_in_prompt"]]
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            show(r)
            print()
    if bad:
        print("PROMPT BUDGET PROBLEMS:")
        for b in bad:
            print("  -", b)
        return 1
    if not a.json:
        print("prompt budget: %d store(s) checked, every rule marker the prompt carried is still reachable"
              % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
