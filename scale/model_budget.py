#!/usr/bin/env python3
"""Per-account model budget: what this tenant has spent today, and what it may do next.

WHY THIS FILE EXISTS
Every other ceiling in this product bounds BEHAVIOUR - how many applications go out (the interview
backoff), how often mail is read (the monitor), how many employer emails one run may send
(notify.json's application_email.max_per_*). None of them bounds MONEY. Measured on 22 Sep 2026:
one candidate's sweeps and mailbox runs cost $2.68 in 24 hours against a $39/month plan - $80/month
at that rate, twice what the account pays. Nothing noticed, because nothing added the spend up per
account. That is the gap this gate closes.

It answers two questions for a run that is about to start:
  * may I run at all?      -> exit 0 yes, exit 70 no (the subscriber set budget.on_exceed: stop)
  * and at what volume?    -> a NUMBER on stdout: the application cap this run may use
and it keeps the ledger that makes the answer possible: one line per run, in the tenant's own state,
with the measured token counts, the model, the run id and the cost in USD.

WHERE THE NUMBERS COME FROM
The agent cannot weigh its own tokens, so nothing here is self-reported. Each run's usage is read
from the engine's own audit (`<profile>/cron/usage_audit.jsonl`: one line per agent run, with ts,
job, prompt_tokens, completion_tokens, model) and priced with the product's one two-tier cost model
(tools/price_model.py: input 0.098, output 0.196, cache-read 0.028 USD per 1M tokens at a measured
99.5% cache-hit ratio - every run bills almost entirely input, and almost all of it cached).
`record` sums the audit lines that belong to THIS run and appends them to

    <workspace>/data/usage.jsonl

one line per run, beside this product's other per-run ledgers (data/apply-email-ledger.json,
data/notify-ledger.jsonl). The dashboard's Cost panel and tools/cost_report.py read the same file, so
the subscriber, the operator and the gate can never disagree about the total. `--ledger` and
$JHA_USAGE_LEDGER move it.

THE DIAL IS NEVER FATAL
This runs unattended, in the middle of a paid customer's sweep, so a budget block that is missing,
truncated or hand-edited into nonsense degrades to the built-in default, says so (`degraded` in
`status --json`, and on stderr from `ask`), and NEVER changes the run's volume: a broken dial must
not silently slow a paying hunt. `stop` is the only setting that can end a run, and only while the
subscriber has asked for it.

Usage
  python3 gates/model_budget.py ask --plan-cap 10                   # the cap to use now
  python3 gates/model_budget.py ask --plan-cap 10 --json             # the same, machine-readable
  python3 gates/model_budget.py record --job jane-doe-job-hunt \
      --since 2026-09-22T22:00:00Z --run-id 9d1f...                  # append this run's measured usage
  python3 gates/model_budget.py record --tokens-in 4200000 --tokens-out 51000   # or a known figure
  python3 gates/model_budget.py status [--json]                      # today's spend and the dial
  python3 gates/model_budget.py line                                 # just the sentence, or nothing

Exit codes (the same family the other gates use)
  0  within budget: the full cap applies
  72 a budget has been reached: the reduced cap applies (a decision, not an error)
  70 the `stop` dial is doing its job: do NOT run this sweep
  2  usage error
  3  dependency missing (record: no usage audit matched, so nothing was written)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE.parent                      # the workspace, exactly as interview_backoff reads it

# ---------------------------------------------------------------- the product's cost model
# Carried verbatim from tools/price_model.py, which a provisioned workspace does not have: the repo
# does not exist on a customer host. tests/test_model_budget.py asserts these literals equal
# price_model's own, and that run_cost() agrees with price_model.run_cost() on every sample - which is
# what keeps one formula from quietly becoming two.
RATES = {"input": 0.098, "output": 0.196, "cache_read": 0.028}
CACHE_HIT_RATIO = 0.995

# ---------------------------------------------------------------- the dial's built-in default
# Used only when the dial is absent or unreadable. `warn` on purpose: a broken budget file must never
# change what an unattended run does, it must only be visible. The shipped config sets the real dial.
DEFAULT_DAILY_USD = 1.00
DEFAULT_ON_EXCEED = "warn"
DEFAULT_THROTTLE_RATE = 0.25
EXCEED_ACTIONS = ("warn", "throttle", "stop")
NEAR_LIMIT = 0.8                        # from here on the sentence says the budget is nearly spent
MAX_SANE_DAILY_USD = 10_000.0           # a "budget" above this is a typo, not a limit

# The tenant's own state, in the same directory as the product's other per-run ledgers.
LEDGER_REL = pathlib.Path("data") / "usage.jsonl"
# Where the runtime keeps this tenant's dials. notify.json is the file the engine already reads
# (engine/notify/apply_email.py: "read from the workspace's own notify.json first - that is what the
# runtime uses"), with config.json as the same-shape fallback it also consults. No third file.
RUNTIME_DIAL_FILES = ("notify.json", "config.json")
DIAL_KEY = "budget"
DEFAULT_MODEL = "deepseek-v4-flash"
SWEEP_PROMPT_TOKENS = 2_000_000         # the same split cost_report.py and the dashboard classify by
MAIL_PROMPT_TOKENS = 100_000


class BudgetError(Exception):
    """A refusal the caller should read, never a traceback."""


def run_cost(prompt_tokens, completion_tokens, hit_ratio: float = CACHE_HIT_RATIO) -> float:
    """USD for one agent run at the provider's two-tier input pricing."""
    prompt_tokens = max(0, int(prompt_tokens or 0))
    completion_tokens = max(0, int(completion_tokens or 0))
    hits = prompt_tokens * hit_ratio
    misses = prompt_tokens - hits
    return (hits / 1e6) * RATES["cache_read"] + (misses / 1e6) * RATES["input"] \
        + (completion_tokens / 1e6) * RATES["output"]


def kind_for(prompt_tokens) -> str:
    """sweep | mail | run - the same thresholds the dashboard and cost_report.py classify by."""
    prompt_tokens = int(prompt_tokens or 0)
    if prompt_tokens > SWEEP_PROMPT_TOKENS:
        return "sweep"
    if prompt_tokens > MAIL_PROMPT_TOKENS:
        return "mail"
    return "run"


# ---------------------------------------------------------------- paths
def workspace_of(explicit: str = "") -> pathlib.Path:
    """The tenant workspace: --workspace, else $JHA_WORKSPACE, else the gate's own parent directory."""
    raw = str(explicit or os.environ.get("JHA_WORKSPACE", "") or "").strip()
    return pathlib.Path(raw).expanduser() if raw else BASE


def slug_for(workspace) -> str:
    """The account's own name for a ledger line: the candidate/profile folder, never the literal "workspace".

    A provisioned workspace is `<profile>/workspace`, so the directory name alone would file every tenant's
    spend under "workspace" - the one label that is identical for every account on the host.
    """
    ws = pathlib.Path(workspace or workspace_of())
    if ws.name in ("workspace", "hunts") and ws.parent.name:
        return ws.parent.name
    return ws.name


def ledger_path(workspace=None, explicit: str = "") -> pathlib.Path:
    raw = str(explicit or os.environ.get("JHA_USAGE_LEDGER", "") or "").strip()
    if raw:
        return pathlib.Path(raw).expanduser()
    return pathlib.Path(workspace or workspace_of()) / LEDGER_REL


def dial_files(workspace) -> list:
    """The runtime dial files, in the order the rest of the engine reads them."""
    ws = pathlib.Path(workspace or workspace_of())
    return [ws / name for name in RUNTIME_DIAL_FILES]


def carry_path(workspace) -> pathlib.Path:
    """The file a dial change is written to.

    notify.json wins if it already carries a budget block (an operator may have put one there by
    hand, and an unattended run must read the file that already speaks); otherwise config.json is
    created for it - the same two names apply_email.load_config consults, so no third file appears.
    """
    ws = pathlib.Path(workspace or workspace_of())
    notify = ws / "notify.json"
    if notify.is_file():
        try:
            data = json.loads(notify.read_text(encoding="utf-8", errors="replace") or "{}")
            if isinstance((data or {}).get(DIAL_KEY), dict):
                return notify
        except (OSError, ValueError):
            pass
    return ws / "config.json"


# ---------------------------------------------------------------- the dial
def _usd(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    # isfinite, not just inequality: float("nan") passes every comparison, and a NaN budget would ride
    # into the dashboard's JSON as an invalid literal
    if not math.isfinite(number) or number <= 0 or number > MAX_SANE_DAILY_USD:
        return None
    return number


def _rate(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if 0 < number <= 1 else None


def _action(value):
    text = str(value or "").strip().lower()
    return text if text in EXCEED_ACTIONS else None


def load_budget(workspace=None, cfg=None) -> dict:
    """The tenant's budget dial, with the built-in default behind every missing or unreadable value.

    Sources, in the order the runtime reads them: the workspace's own notify.json, its config.json,
    then a tenant config handed in by a caller (`--config`, the dashboard, a test). Never raises: every
    unusable value is reported in `degraded` instead, because the alternative is an unattended sweep
    dying on a typo in a file the customer can edit.
    """
    out = {"daily_usd": DEFAULT_DAILY_USD, "on_exceed": DEFAULT_ON_EXCEED,
           "throttle_rate": DEFAULT_THROTTLE_RATE, "source": "built-in defaults", "degraded": [],
           "explicit": False, "_action_set": False, "_rate_set": False}
    sources = []
    for path in dial_files(workspace):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
        except (OSError, ValueError) as exc:
            out["degraded"].append(f"{path.name} is not valid JSON ({exc}); its budget block was ignored")
            continue
        block = (data or {}).get(DIAL_KEY) if isinstance(data, dict) else None
        if isinstance(block, dict):
            sources.append((str(path), block))
        elif block is not None:
            out["degraded"].append(f"{path.name}: budget must be a block with daily_usd/on_exceed, "
                                   f"got {type(block).__name__}")
    if isinstance(cfg, dict) and isinstance(cfg.get(DIAL_KEY), dict):
        sources.append(("the tenant config", cfg[DIAL_KEY]))

    for source, block in sources:
        usd = _usd(block.get("daily_usd"))
        if usd is not None:
            if not out["explicit"]:
                out["daily_usd"] = usd
                out["source"] = source
                out["explicit"] = True
        elif block.get("daily_usd") not in (None, ""):
            out["degraded"].append(f"{source}: budget.daily_usd {block.get('daily_usd')!r} is not a "
                                   f"positive number under {MAX_SANE_DAILY_USD:.0f}; using the default "
                                   f"${DEFAULT_DAILY_USD:.2f}")
        action = _action(block.get("on_exceed"))
        if action is not None:
            if not out["_action_set"]:
                out["on_exceed"] = action
                out["_action_set"] = True
                if not out["explicit"]:
                    out["source"] = source
        elif block.get("on_exceed") not in (None, ""):
            out["degraded"].append(f"{source}: budget.on_exceed {block.get('on_exceed')!r} is not one of "
                                   f"{list(EXCEED_ACTIONS)}; using {DEFAULT_ON_EXCEED}")
        rate = _rate(block.get("throttle_rate"))
        if rate is not None:
            if not out["_rate_set"]:
                out["throttle_rate"] = rate
                out["_rate_set"] = True
        elif block.get("throttle_rate") not in (None, ""):
            out["degraded"].append(f"{source}: budget.throttle_rate {block.get('throttle_rate')!r} is not a "
                                   f"share between 0 and 1; using {DEFAULT_THROTTLE_RATE}")
    if not sources:
        names = ", ".join(path.name for path in dial_files(workspace))
        out["degraded"].append(f"no budget block in the workspace dial files ({names}): using the built-in "
                               f"default of ${DEFAULT_DAILY_USD:.2f}/day, on_exceed={DEFAULT_ON_EXCEED}")
    out.pop("_action_set", None)
    out.pop("_rate_set", None)
    return out


def write_budget(workspace, daily_usd=None, on_exceed=None, throttle_rate=None) -> pathlib.Path:
    """Carry a dial change into the workspace file the runtime reads. Merges, never clobbers."""
    path = carry_path(workspace)
    data = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
        except ValueError as exc:
            raise BudgetError(f"{path} is not valid JSON, refusing to rewrite it ({exc})")
    if not isinstance(data, dict):
        raise BudgetError(f"{path} is not a JSON object")
    block = dict(data.get(DIAL_KEY) or {})
    if daily_usd is not None:
        block["daily_usd"] = round(float(daily_usd), 4)
    if on_exceed is not None:
        block["on_exceed"] = str(on_exceed)
    if throttle_rate is not None:
        block["throttle_rate"] = float(throttle_rate)
    block.setdefault("_comment", "The per-account model budget. The engine enforces it before a sweep "
                                 "spends anything; the tenant config is the source of truth, and this "
                                 "copy is what an unattended run reads.")
    data[DIAL_KEY] = block
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


# ---------------------------------------------------------------- the ledger
def load_lines(path) -> list:
    """Every readable JSON object in a ledger, junk lines skipped rather than fatal."""
    if not path:
        return []
    path = pathlib.Path(path)
    out = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            out.append(record)
    return out


def spend_today(ledger=None, today: str = "") -> dict:
    """Today's measured spend (UTC), summed from the tenant's own ledger.

    A line without a cost_usd is priced from its token counts, so a hand-written or older line still
    counts. An unreadable ledger is zero spend, never an exception: the sweep continues either way.
    """
    today = today or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    out = {"day": today, "runs": 0, "cost": 0.0, "prompt_tokens": 0, "completion_tokens": 0,
           "sweeps": 0, "mail": 0, "last_ts": "", "unreadable": 0}
    for record in load_lines(ledger):
        ts = str(record.get("ts") or "")
        if not ts:
            out["unreadable"] += 1
            continue
        if ts[:10] != today:
            continue
        pt = int(record.get("prompt_tokens") or 0)
        ct = int(record.get("completion_tokens") or 0)
        try:
            cost = float(record.get("cost_usd"))
        except (TypeError, ValueError):
            cost = run_cost(pt, ct)
        if not math.isfinite(cost):
            cost = run_cost(pt, ct)     # a hand-edited "NaN" must not poison every later sum
        out["runs"] += int(record.get("runs") or 1)
        out["cost"] += cost
        out["prompt_tokens"] += pt
        out["completion_tokens"] += ct
        if pt > SWEEP_PROMPT_TOKENS:
            out["sweeps"] += 1
        elif pt > MAIL_PROMPT_TOKENS:
            out["mail"] += 1
        out["last_ts"] = max(out["last_ts"], ts)
    out["cost"] = round(out["cost"], 6)
    return out


def volume_for(plan_cap, action, throttle_rate=DEFAULT_THROTTLE_RATE) -> int:
    """The application cap for this run. Rounds rather than truncates, and never throttles to 0.

    The same arithmetic the interview backoff uses for its cap: a reduced run must look like a slower
    hunt, not a stopped one - only `stop` may return 0, and only because the subscriber asked for it.
    """
    plan_cap = int(plan_cap)
    if plan_cap <= 0:
        return 0
    if action == "stop":
        return 0
    if action == "throttle":
        return max(1, int(round(plan_cap * (_rate(throttle_rate) or DEFAULT_THROTTLE_RATE))))
    return plan_cap


# ---------------------------------------------------------------- state
def describe(spent, budget_usd, action, throttle_rate, volume=None, plan_cap=None) -> str:
    """One sentence a human reads: the spend, the line, and how to change it."""
    if action == "ok" and spent < NEAR_LIMIT * budget_usd:
        return ""
    reset = "The budget resets at 00:00 UTC."
    if action == "stop":
        return (f"Today's model spend is ${spent:.2f}, at the ${budget_usd:.2f} daily budget on this "
                f"account, so this sweep does not run. Raise budget.daily_usd in Settings to continue. "
                f"{reset}")
    if action == "throttle":
        pct = int(round((_rate(throttle_rate) or DEFAULT_THROTTLE_RATE) * 100))
        at = f" ({volume} of {plan_cap})" if volume is not None and plan_cap else ""
        return (f"Today's model spend is ${spent:.2f} of the ${budget_usd:.2f} daily budget, so this "
                f"sweep applies at {pct}% of the usual cap{at}. Full volume resumes after the budget "
                f"resets at 00:00 UTC.")
    if spent >= budget_usd:
        return (f"Today's model spend is ${spent:.2f} of the ${budget_usd:.2f} daily budget. Nothing is "
                f"throttled (budget.on_exceed is 'warn'); set it to throttle or stop in Settings to "
                f"bound it. {reset}")
    return (f"Today's model spend is ${spent:.2f} of the ${budget_usd:.2f} daily budget - one more sweep "
            f"would cross it. {reset}")


def state(workspace=None, cfg=None, plan_cap=None, today: str = "", ledger_override: str = "") -> dict:
    """Everything a caller needs about the account's money: the dial, today's spend, and the volume.

    Never raises. An unreadable ledger is zero spend with a `degraded` note; an unreadable dial is the
    built-in default with a `degraded` note and action `warn`, so a broken file cannot slow a run.
    """
    degraded = []
    try:
        workspace = pathlib.Path(workspace or workspace_of())
    except Exception as exc:                                    # pragma: no cover - defensive
        degraded.append(f"workspace unusable ({exc})")
        workspace = BASE
    try:
        dial = load_budget(workspace, cfg)
        degraded += dial["degraded"]
    except Exception as exc:                                    # pragma: no cover - defensive
        degraded.append(f"the budget dial could not be read ({exc}); using the built-in default")
        dial = {"daily_usd": DEFAULT_DAILY_USD, "on_exceed": DEFAULT_ON_EXCEED,
                "throttle_rate": DEFAULT_THROTTLE_RATE, "source": "built-in defaults", "explicit": False}
    ledger = ledger_path(workspace, ledger_override)
    try:
        spent = spend_today(ledger, today)
    except Exception as exc:                                    # pragma: no cover - defensive
        degraded.append(f"the usage ledger could not be read ({exc}); counting today's spend as $0.00")
        spent = {"day": today or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"), "runs": 0,
                 "cost": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "sweeps": 0, "mail": 0,
                 "last_ts": "", "unreadable": 0}
    if spent["unreadable"]:
        degraded.append(f"{spent['unreadable']} ledger line(s) carry no timestamp and were skipped")

    budget_usd = float(dial["daily_usd"])
    exhausted = spent["cost"] >= budget_usd
    # A broken dial warns, it never throttles or stops: something is wrong with a file, not with the
    # customer's spending, and an unattended run must not pay for that.
    action = dial["on_exceed"] if (exhausted and dial["explicit"]) else ("warn" if exhausted else "ok")
    volume = volume_for(plan_cap, action, dial["throttle_rate"]) if plan_cap is not None else None
    return {
        "state": {"action": action, "exhausted": bool(exhausted),
                  "near_limit": bool(not exhausted and spent["cost"] >= NEAR_LIMIT * budget_usd),
                  "ok_to_run": action != "stop"},
        "budget": {"daily_usd": round(budget_usd, 4), "on_exceed": dial["on_exceed"],
                   "throttle_rate": dial["throttle_rate"], "source": dial["source"],
                   "explicit": bool(dial["explicit"]), "defaults": not dial["explicit"],
                   "options": list(EXCEED_ACTIONS)},
        "spent_today_usd": round(spent["cost"], 4),
        "remaining_usd": round(max(0.0, budget_usd - spent["cost"]), 4),
        "ratio": round(spent["cost"] / budget_usd, 4) if budget_usd else 0.0,
        "runs_today": spent["runs"], "sweeps_today": spent["sweeps"], "mail_today": spent["mail"],
        "tokens_today": spent["prompt_tokens"] + spent["completion_tokens"],
        "last_ts": spent["last_ts"], "day": spent["day"],
        "action": action, "volume": volume, "plan_cap": plan_cap,
        "line": describe(spent["cost"], budget_usd, action, dial["throttle_rate"], volume, plan_cap),
        "rates_usd_per_mtok": dict(RATES), "cache_hit_ratio": CACHE_HIT_RATIO,
        "ledger": str(ledger), "workspace": str(workspace), "degraded": degraded,
        "switch": "budget.daily_usd / budget.on_exceed",
    }


# ---------------------------------------------------------------- record this run's usage
def audit_candidates(workspace, profile: str = "", explicit: str = "") -> list:
    """Where this tenant's per-run usage audit may live, most specific first.

    The same sources engine/scripts/usage_window.py reads: the profile's own cron directory (the file
    holding ONLY this candidate's runs), then the host-wide log the scheduler also writes.
    """
    if explicit:
        return [pathlib.Path(explicit).expanduser()]
    ws = pathlib.Path(workspace or workspace_of())
    names = [n for n in (profile, ws.name, ws.parent.name) if n and n not in ("workspace", "hunts")]
    out = []
    for name in names:
        out.append(pathlib.Path.home() / ".hermes" / "profiles" / name / "cron" / "usage_audit.jsonl")
    out.append(ws.parent / "cron" / "usage_audit.jsonl")
    out.append(pathlib.Path.home() / ".hermes" / "cron" / "usage_audit.jsonl")
    seen, uniq = set(), []
    for path in out:
        if str(path) not in seen:
            seen.add(str(path))
            uniq.append(path)
    return uniq


def parse_ts(value):
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def measure(workspace, since: str = "", job: str = "", profile: str = "", audit: str = "") -> dict:
    """Sum the audit lines belonging to one run: (tokens, model, source) or nothing found.

    Filtered by `--since` (the moment the sweep started) and, when known, by the job's name, so a
    concurrent mailbox run cannot be billed into a sweep's line.
    """
    cutoff = parse_ts(since) if since else None
    for path in audit_candidates(workspace, profile, audit):
        if not path.is_file():
            continue
        prompt = completion = runs = 0
        model = ""
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict) or record.get("error"):
                continue
            when = parse_ts(record.get("ts"))
            if cutoff and (when is None or when < cutoff):
                continue
            if job and job not in str(record.get("job_name") or record.get("job") or ""):
                continue
            prompt += int(record.get("prompt_tokens") or 0)
            completion += int(record.get("completion_tokens") or 0)
            model = model or str(record.get("model") or "")
            runs += 1
        if runs:
            return {"prompt_tokens": prompt, "completion_tokens": completion, "runs": runs,
                    "model": model or DEFAULT_MODEL, "source": str(path)}
    return {"prompt_tokens": 0, "completion_tokens": 0, "runs": 0, "model": DEFAULT_MODEL, "source": ""}


def record(workspace=None, job: str = "", run_id: str = "", since: str = "", profile: str = "",
           audit: str = "", tokens_in=None, tokens_out=None, ledger_override: str = "",
           model: str = "", slug: str = "", now: str = "") -> dict:
    """Append ONE line for this run to the tenant's ledger. Idempotent by run id, never raises."""
    ws = pathlib.Path(workspace or workspace_of())
    ledger = ledger_path(ws, ledger_override)
    if run_id and any(str(line.get("run_id")) == str(run_id) for line in load_lines(ledger)):
        return {"recorded": False, "reason": "this run is already in the ledger", "ledger": str(ledger),
                "run_id": str(run_id)}
    if tokens_in is None or tokens_out is None:
        measured = measure(ws, since=since, job=job, profile=profile, audit=audit)
        if not measured["runs"]:
            return {"recorded": False,
                    "reason": "no usage audit line matched this run, so nothing was written "
                              "(pass --audit, or --tokens-in and --tokens-out)",
                    "ledger": str(ledger),
                    "searched": [str(p) for p in audit_candidates(ws, profile, audit)]}
        tokens_in, tokens_out = measured["prompt_tokens"], measured["completion_tokens"]
        model = model or measured["model"]
        runs, source = measured["runs"], measured["source"]
    else:
        runs, source = 1, "given on the command line"
    cost = run_cost(tokens_in, tokens_out)
    line = {"ts": now or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "slug": slug or slug_for(ws), "run_id": str(run_id or ""), "job": str(job or ""),
            "kind": kind_for(tokens_in), "model": model or DEFAULT_MODEL,
            "prompt_tokens": int(tokens_in or 0), "completion_tokens": int(tokens_out or 0),
            "total_tokens": int(tokens_in or 0) + int(tokens_out or 0), "runs": runs,
            "cost_usd": round(cost, 6), "source": source, "recorded_by": "model_budget.py"}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")
    return {"recorded": True, "line": line, "cost_usd": round(cost, 6), "ledger": str(ledger),
            "model": model or DEFAULT_MODEL}


# ---------------------------------------------------------------- CLI
def _shared(ap):
    ap.add_argument("--workspace", default="", help="the tenant workspace (default: this gate's parent)")
    ap.add_argument("--config", default="", help="a tenant config to read the dial from as well")
    ap.add_argument("--ledger", default="", help="the usage ledger (default: <workspace>/data/usage.jsonl)")


def _cfg(path: str):
    """A tenant config, or None. An unreadable one is None, never an exception."""
    if not path:
        return None
    try:
        text = pathlib.Path(path).expanduser().read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _exit_code(st) -> int:
    if not st["budget"]["explicit"]:
        return 0        # a degraded dial never changes what the run does
    return {"stop": 70, "throttle": 72}.get(st["action"], 0)


def cmd_ask(a) -> int:
    st = state(workspace=a.workspace, cfg=_cfg(a.config), plan_cap=a.plan_cap,
               ledger_override=a.ledger)
    if a.json:
        print(json.dumps({k: st[k] for k in ("action", "volume", "plan_cap", "spent_today_usd",
                                             "budget", "remaining_usd", "line", "degraded")}, indent=1))
    else:
        print(st["volume"])
        if st["line"]:
            print(f"# {st['line']}", file=sys.stderr)
    for note in st["degraded"]:
        print(f"# budget degraded: {note}", file=sys.stderr)
    return _exit_code(st)


def cmd_record(a) -> int:
    result = record(workspace=a.workspace, job=a.job, run_id=a.run_id, since=a.since,
                    profile=a.profile, audit=a.audit, tokens_in=a.tokens_in, tokens_out=a.tokens_out,
                    ledger_override=a.ledger, model=a.model, slug=a.slug)
    if not result["recorded"]:
        print(f"model_budget: not recorded: {result['reason']}", file=sys.stderr)
        return 3 if "no usage audit" in result["reason"] else 0
    line = result["line"]
    print(f"{line['kind']} run recorded: ${result['cost_usd']:.4f} "
          f"({line['prompt_tokens']:,} in / {line['completion_tokens']:,} out, {line['model']}) "
          f"-> {result['ledger']}")
    return 0


def cmd_status(a) -> int:
    st = state(workspace=a.workspace, cfg=_cfg(a.config), plan_cap=a.plan_cap, ledger_override=a.ledger)
    if a.json:
        print(json.dumps(st, indent=1))
        return 0
    b = st["budget"]
    print(f"model budget: ${b['daily_usd']:.2f}/day, on_exceed={b['on_exceed']}"
          f" (from {b['source']}{', DEGRADED to the defaults' if b['defaults'] else ''})")
    print(f"today ({st['day']} UTC): ${st['spent_today_usd']:.2f} spent, {st['runs_today']} runs "
          f"({st['sweeps_today']} sweeps, {st['mail_today']} mailbox), ${st['remaining_usd']:.2f} left")
    print(f"ledger: {st['ledger']}")
    if st["line"]:
        print(st["line"])
    for note in st["degraded"]:
        print(f"  degraded: {note}", file=sys.stderr)
    return _exit_code(st)


def cmd_line(a) -> int:
    st = state(workspace=a.workspace, cfg=_cfg(a.config), plan_cap=a.plan_cap, ledger_override=a.ledger)
    if st["line"]:
        print(st["line"])
        return _exit_code(st)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="per-account model budget and usage ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_ask = sub.add_parser("ask", help="may this run start, and at what volume")
    _shared(p_ask)
    p_ask.add_argument("--plan-cap", type=int, default=None,
                       help="the cap this run would otherwise use; the answer is a number no higher")
    p_ask.add_argument("--json", action="store_true")
    p_rec = sub.add_parser("record", help="append this run's measured usage to the ledger")
    _shared(p_rec)
    p_rec.add_argument("--job", default="", help="the job this run is (filters the audit)")
    p_rec.add_argument("--run-id", default="", help="this run's id; a repeat is refused, never double-counted")
    p_rec.add_argument("--since", default="", help="ISO time the run started (only later audit lines count)")
    p_rec.add_argument("--profile", default="", help="the Hermes profile owning the usage audit")
    p_rec.add_argument("--audit", default="", help="an explicit usage_audit.jsonl")
    p_rec.add_argument("--tokens-in", type=int, default=None)
    p_rec.add_argument("--tokens-out", type=int, default=None)
    p_rec.add_argument("--model", default="")
    p_rec.add_argument("--slug", default="")
    p_st = sub.add_parser("status", help="today's spend, the dial, and the sentence")
    _shared(p_st)
    p_st.add_argument("--plan-cap", type=int, default=None)
    p_st.add_argument("--json", action="store_true")
    p_line = sub.add_parser("line", help="just the sentence, or nothing")
    _shared(p_line)
    p_line.add_argument("--plan-cap", type=int, default=None)
    a = ap.parse_args(argv)
    return {"ask": cmd_ask, "record": cmd_record, "status": cmd_status, "line": cmd_line}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
