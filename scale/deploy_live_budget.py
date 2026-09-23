#!/usr/bin/env python3
"""Install the model-budget gate into the live tenant workspaces and start their ledgers.

The live sweep prompts now ask `<ws>/gates/model_budget.py`, so the file has to be there or every run fails
that step and no ledger line is ever written. This also carries the dial into each workspace (nothing else
can reach it) and backfills today's already-incurred spend from each profile's own usage audit, so the day's
figure is real from the first look rather than from the first sweep after the install.

  python3 deploy_live_budget.py            # do it
  python3 deploy_live_budget.py --check     # report only
"""
from __future__ import annotations

import datetime
import importlib.util
import pathlib
import shutil
import sys

REPO = pathlib.Path("/home/ubuntu/jobhunt-agent")
GATE_SRC = REPO / "engine" / "gates" / "model_budget.py"
PROFILES = pathlib.Path("/home/ubuntu/.hermes/profiles")
# The dial for the running accounts: WARN, at a level just above this account's own measured burn, because
# the owner's standing instruction is that cost must never slow a hunt. Measured 22 Sep 2026: $2.68/day for
# vishal against a $39/month plan, and the plans' own cost basis is ~$0.40/day - so this reports the gap
# without changing what a sweep does until the owner raises it to throttle or stop.
DIAL = {"daily_usd": 3.00, "on_exceed": "warn", "throttle_rate": 0.25}


def load_gate():
    spec = importlib.util.spec_from_file_location("jha_gate_deploy", GATE_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(apply: bool) -> int:
    mb = load_gate()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    for profile in sorted(p for p in PROFILES.iterdir() if (p / "workspace").is_dir()):
        ws = profile / "workspace"
        dst = ws / "gates" / GATE_SRC.name
        line = [f"{profile.name}: "]
        if apply:
            shutil.copy2(GATE_SRC, dst)
            dst.chmod(0o755)
        line.append(f"gate {'installed' if dst.is_file() else 'MISSING'}")
        if apply:
            carried = mb.write_budget(ws, daily_usd=DIAL["daily_usd"], on_exceed=DIAL["on_exceed"],
                                      throttle_rate=DIAL["throttle_rate"])
            line.append(f"dial -> {carried.name}")
        state = mb.state(workspace=str(ws), cfg={})
        line.append(f"spent_today=${state['spent_today_usd']:.2f} runs_today={state['runs_today']} "
                    f"degraded={len(state['degraded'])}")
        if apply and state["runs_today"] == 0:
            back = mb.record(workspace=str(ws), profile=profile.name, since=today,
                             run_id=f"backfill-{state['day']}")
            line.append("backfilled today's runs" if back["recorded"]
                        else f"backfill refused ({back['reason'][:60]})")
            state = mb.state(workspace=str(ws), cfg={})
            line.append(f"spent_today=${state['spent_today_usd']:.2f} runs_today={state['runs_today']}")
        print(" ".join(line))
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" not in sys.argv))
