#!/usr/bin/env python3
"""Self-service dashboard for a hunt: every knob, every outcome, in one place.

Stdlib only. One page plus a JSON API over the tenant's own files:

  GET  /                        the UI
  GET  /api/healthz             liveness
  GET  /api/state               config dials, plan, job status, counters (the original shape)
  GET  /api/overview            is the hunt live: per-job schedule / last run / next run / last
                                outcome, tracker counts by status, applications this month, actions
  GET  /api/applications        tracker rows: search with ?q=, filter with ?status=
  GET  /api/applications/<id>   one row in full: company, role, status, key dates, notes, apply URL
  GET  /api/usage               measured spend, per-run cost, plan limits, remaining allowance
  GET  /api/cost                the same figures, named for the cost panel
  GET  /api/billing             plan, licence key STATE (never the key), checkout link, invoices
  GET  /api/config/dials        the dials the customer owns, with their allowed values
  GET  /api/control             the one-click actions, and whether each needs the token
  GET  /api/notify              alert channels, config summary, ledger counts
  POST /api/config/preview      what a change would do: diff + validation, writes nothing (open)
  POST /api/config              apply dial changes (token): a rejected change rolls back
  POST /api/control/pause       pause every job of this tenant (token)
  POST /api/control/resume      resume them (token)
  POST /api/control/sweep       queue the sweep now, through the scheduler's own CLI (token)
  POST /api/control/alert-test  send a self-test alert through the notifier (token)
  POST /api/control/channels    switch the alert channels (token)
  POST /api/control/sheet-sync    run this tenant's sheets job now: row store -> Google Sheet (token)
  POST /api/notify/test         legacy route, same code path as control/alert-test (token)
  POST /api/notify/channels     legacy route, same code path as control/channels (token)
  POST /api/jobs/<name>         resume | pause one job (token)

Reads are open; every write needs the X-Dashboard-Token header. Nothing here sends mail through
the candidate's mailbox, and no endpoint returns a credential: responses carry counts, statuses,
presence booleans and fields the owner set themselves. Every JSON body is run through a scrubber
before it leaves, so a token a subprocess echoed cannot reach the browser.

  DASHBOARD_TOKEN=... python3 dashboard/server.py --tenant config/tenant.yaml --port 8787
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import urllib.error
import urllib.request
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
except ImportError:  # pragma: no cover
    raise SystemExit("python3.7+ required")

# This module sits beside the server: tenancy resolves a request's session to a user's own tenant.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tenancy import Tenancy, TenancyError  # noqa: E402

from provisioning.provision_tenant import (EU27, read_config, read_config_minimal,  # noqa: E402
                                          validate, workspace_for)

NOTIFY_DIR = ROOT / "engine" / "notify"
GATES_DIR = ROOT / "engine" / "gates"
if str(GATES_DIR) not in sys.path:
    sys.path.insert(0, str(GATES_DIR))
if str(NOTIFY_DIR) not in sys.path:
    sys.path.insert(0, str(NOTIFY_DIR))
from tools.price_model import RATES, run_cost  # noqa: E402

PRICING_FILE = ROOT / "pricing.yaml"
USAGE_DIR = ROOT / "usage"
APP_DIR = ROOT / "dashboard" / "app"

# The model-budget gate's own vocabulary, imported rather than restated, so the Settings screen cannot
# offer a value the engine would refuse and the default the interface shows is the one the gate really
# falls back to. A checkout without the gate still serves every other panel.
try:
    import model_budget as _model_budget

    MODEL_BUDGET_ACTIONS = tuple(_model_budget.EXCEED_ACTIONS)
    MODEL_BUDGET_DEFAULT_USD = _model_budget.DEFAULT_DAILY_USD
except Exception:  # pragma: no cover - only a checkout that is missing the gate
    _model_budget = None
    MODEL_BUDGET_ACTIONS = ("warn", "throttle", "stop")
    MODEL_BUDGET_DEFAULT_USD = 1.00

# The three permissions the sign-in screen asks for, and nothing else: reading mail to triage replies, reading
# the calendar to confirm interview slots, and the tracker's own spreadsheet. Sending mail and writing documents
# are requested separately by the engine, only when the candidate turns the email route on.
# Reachable without a session, because they are how a session is obtained.
LOGIN_OPEN_ROUTES = ("/api/auth/start", "/api/auth/me", "/api/auth/logout", "/auth/callback",
                     "/api/healthz", "/api/version")

SIGN_IN_SCOPES = (
    ("https://www.googleapis.com/auth/gmail.readonly", "Gmail",
     "Read-only, to triage replies and detect interview invites"),
    ("https://www.googleapis.com/auth/calendar", "Google Calendar",
     "To schedule and show interview alerts"),
    ("https://www.googleapis.com/auth/spreadsheets", "Google Sheets",
     "This is where the application tracker lives"),
)
ALERT_STATUSES = ("Interview", "Offer")
HOST_HOME = pathlib.Path(os.environ.get("HERMES_HOME", pathlib.Path.home() / ".hermes")).expanduser()           # overridable so a test can point at a scratch meter
BILLING_DIR = ROOT / "billing"

STATUS_ORDER = ["Interview", "Offer", "Submitted", "Emailed", "Queued", "Blocked",
                "Skipped", "Rejected", "In progress"]
# Rows that count as "an application": the engine only reaches these after it really applied.
APPLIED_STATUSES = {"Submitted", "Emailed", "Interview", "Offer"}
CHANNELS = ("telegram", "email", "webhook", "local")
CADENCE_OPTIONS = ["every 720m", "every 360m", "every 180m", "every 120m", "every 60m"]
# The alert thresholds documented in config/tenant.example.yaml. Unknown values already in a
# tenant's file are preserved and reported, never silently dropped.
PING_OPTIONS = ["interview_invite", "offer", "action_required"]
HEX12 = re.compile(r"^[0-9a-f]{12} \[")
SHEET_JOB = "{slug}-tracker-sheets-sync"
SHEET_JOB_ALIASES = ("{slug}-sheets-sync",)
SWEEP_JOB = "{slug}-job-hunt"        # engine/cron/jobs.template.json names

# Resolved at startup (--hermes-bin, JHA_HERMES_BIN, then PATH). Tests point this at a shim so the
# real CLI shape is asserted without touching a live scheduler.
HERMES_BIN = ""

# Anything that looks like a credential, scrubbed from every response body before it is sent.
SECRET_PATTERNS = (
    (re.compile(r"\d{8,12}:[A-Za-z0-9_-]{30,}"), "[telegram-token]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{12,}"), "[api-key]"),
    (re.compile(r"whsec_[A-Za-z0-9]{8,}"), "[webhook-secret]"),
    (re.compile(r"JHA1\.[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+"), "[licence-key]"),
)


# ---------------------------------------------------------------- small helpers
def _now_month() -> str:
    return time.strftime("%Y-%m")


def _tail(text: str, limit: int = 600) -> str:
    text = " ".join(str(text).split())
    return text[-limit:]


def _scrub(text, extra=()) -> str:
    """Mask anything credential-shaped. A subprocess may echo a token; the browser must not see it."""
    out = str(text)
    for pat, rep in SECRET_PATTERNS:
        out = pat.sub(rep, out)
    for value in extra:
        value = str(value or "")
        if len(value) >= 8:
            out = out.replace(value, "[redacted]")
    return out


def _iso_date(epoch) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(int(epoch)))
    except Exception:
        return ""


def _days_left(epoch) -> int | None:
    try:
        return int((int(epoch) - time.time()) / 86400)
    except Exception:
        return None


def _license_module():
    """billing/license.py, loaded by path: `import license` would shadow the builtin."""
    spec = importlib.util.spec_from_file_location("jha_license", BILLING_DIR / "license.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def scheduler_missing(binary: str) -> str:
    """The reason the scheduler cannot be used, or "" when it can."""
    if not binary:
        return ("the scheduler CLI (hermes) is not on this host's PATH, so nothing was queued; "
                "start the dashboard with --hermes-bin <path> if it lives somewhere else")
    if not pathlib.Path(binary).exists():
        return f"the scheduler CLI is not on this host: {binary}"
    return ""


def hermes_bin() -> str:
    """Where the scheduler CLI lives. Empty string means this host cannot queue work."""
    if HERMES_BIN:
        return HERMES_BIN
    found = shutil.which("hermes")
    if found:
        return found
    local = pathlib.Path.home() / ".local" / "bin" / "hermes"
    return str(local) if local.exists() else ""


def profile_for(cfg: dict) -> str:
    slug = (cfg.get("tenant") or {}).get("slug", "default")
    return ((cfg.get("paths") or {}).get("profile", slug) or slug).format(slug=slug)


def run_command(cmd: list[str], cwd: pathlib.Path | None = None, timeout: int = 60) -> dict:
    """Run a real command and report exactly what happened. Never invents an outcome.

    `out` keeps the raw text because callers parse it (the scheduler's job listing is line-based);
    `tail` is the collapsed one-liner a message or a JSON field should carry.
    """
    if not cmd or not cmd[0]:
        return {"ok": False, "rc": 127, "out": "no command available on this host",
                "tail": "no command available on this host"}
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError:
        msg = f"not found: {cmd[0]}"
        return {"ok": False, "rc": 127, "out": msg, "tail": msg}
    except subprocess.TimeoutExpired:
        msg = f"timed out after {timeout}s"
        return {"ok": False, "rc": 124, "out": msg, "tail": msg}
    except OSError as e:
        msg = f"could not run {cmd[0]}: {e}"
        return {"ok": False, "rc": 126, "out": msg, "tail": msg}
    out = ((p.stdout or "") + (p.stderr or "")).strip()[:8000]
    return {"ok": p.returncode == 0, "rc": p.returncode, "out": out,
            "tail": _tail(out, 600) or "(no output)"}


# ---------------------------------------------------------------- data access
def tenant_cfg(path: pathlib.Path) -> dict:
    return read_config(path) if path.exists() else {}


def _row_reader():
    """The shared row-store reader (engine/tools/verify_tracker.py) when it is reachable.

    One reader for every consumer: the sheets sync, the agents' verifier and this panel must count
    the same rows from the same file, and a hand-wrapped row must not vanish from the panel the way
    a line scanner drops it.
    """
    import importlib.util

    for cand in (ROOT / "engine" / "tools" / "verify_tracker.py",
                 ROOT / "tools" / "verify_tracker.py",
                 pathlib.Path.home() / ".hermes" / "scripts" / "verify_tracker.py",
                 *sorted(pathlib.Path.home().glob(
                     ".hermes/profiles/*/skills/productivity/job-application/scripts/verify_tracker.py"))):
        try:
            if cand.is_file():
                spec = importlib.util.spec_from_file_location("jha_verify_tracker", cand)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                return mod
        except Exception:
            continue
    return None


ROW_KEYS = ("id", "company", "role", "location", "fit", "status", "ats", "tailored_cv",
            "cover_letter", "hr_email", "apply_url", "notes")


def tracker_rows(ws: pathlib.Path) -> list[dict]:
    """The rows in this workspace's row store: engine data, never a workbook.

    The row store is what the candidate's Google Sheet is built from, so this count matches the
    sheet's whenever the sync is current. The line-scan fallback below exists only for an install
    that does not ship the shared reader.
    """
    ver = _row_reader()
    if ver is not None:
        try:
            _headers, rows = ver.read_rows(ws / "build_tracker.py")
            return [dict(zip(ROW_KEYS, list(r) + [""] * (len(ROW_KEYS) - len(r)))) for r in rows]
        except Exception:
            return []
    f = ws / "build_tracker.py"
    if not f.exists():
        return []
    rows = []
    for line in f.read_text(errors="replace", encoding="utf-8").splitlines():
        if not re.match(r'\s*\["\d+",', line):
            continue
        if "]" not in line:
            # a hand-edited, wrapped row: skip it rather than take the whole panel down
            continue
        start, end = line.index("["), line.rindex("]") + 1
        try:
            r = ast.literal_eval(line[start:end])
        except Exception:
            continue
        if isinstance(r, list) and len(r) == 12:
            rows.append(dict(zip(("id", "company", "role", "location", "fit", "status", "ats",
                                  "tailored_cv", "cover_letter", "hr_email", "apply_url", "notes"), r)))
    return rows


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: int(r["id"]) if str(r["id"]).isdigit() else 0, reverse=True)


def search_rows(rows: list[dict], q: str) -> list[dict]:
    """Case-insensitive search over the fields a customer can see. Empty query matches everything."""
    q = (q or "").strip().lower()
    if not q:
        return rows
    fields = ("company", "role", "location", "status", "notes", "apply_url", "ats")
    return [r for r in rows if any(q in str(r.get(f, "")).lower() for f in fields)]


def iso_dates(text) -> list[str]:
    return sorted(set(re.findall(r"\d{4}-\d{2}-\d{2}", str(text or ""))))


def application_stats(rows: list[dict], month: str | None = None) -> dict:
    """Applications this month, from the ISO dates the tracker records in each row's notes.

    Honest by construction: a row that was applied to but carries no date is reported as
    `undated` instead of being counted twice or guessed at. Each row counts once per month it
    mentions, so a row with two dates in one month is still one application.
    """
    month = month or _now_month()
    applied = [r for r in rows if str(r.get("status")) in APPLIED_STATUSES]
    by_month: dict[str, int] = {}
    undated = 0
    this_month = 0
    for r in applied:
        dates = iso_dates(r.get("notes"))
        if not dates:
            undated += 1
        months = {d[:7] for d in dates}
        if month in months:
            this_month += 1
        for m in months:
            by_month[m] = by_month.get(m, 0) + 1
    return {
        "month": month,
        "this_month": this_month,
        "applied_total": len(applied),
        "undated": undated,
        "by_month": dict(sorted(by_month.items(), reverse=True)[:12]),
        "source": "ISO dates in the tracker notes, one application counted once per month",
    }


def plan_entry(plan: str) -> dict:
    if not PRICING_FILE.exists():
        return {}
    doc = json.loads(PRICING_FILE.read_text(encoding="utf-8"))
    return next((p for p in doc["plans"] if p["id"] == plan), {})


def pricing_doc() -> dict:
    return json.loads(PRICING_FILE.read_text(encoding="utf-8")) if PRICING_FILE.exists() else {"plans": [], "policy": {}}


def _profile_dir(cfg_path: pathlib.Path) -> pathlib.Path:
    """The tenant's profile directory (the workspace's parent), where its cron, tokens and ledgers live."""
    ws = _workspace(tenant_cfg(cfg_path))
    return ws.parent if ws.name == "workspace" else ws


def audit_usage(cfg_path: pathlib.Path, month: str) -> dict:
    """Measured spend from the engine's own per-run audit.

    `usage/<slug>.jsonl` is the product meter, written by a managed deployment. On a self-hosted machine the
    scheduler's audit line is what exists: one per agent run, with token counts and a timestamp, so it yields
    both the month's cost and a daily series the cost chart can draw.
    """
    profile = _profile_dir(cfg_path)
    runs, cost = 0, 0.0
    by_day: dict = {}
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "errors": 0, "sweeps": 0, "mail": 0}
    f = profile / "cron" / "usage_audit.jsonl"
    if f.is_file():
        for line in f.read_text(errors="replace", encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            pt, ct = int(d.get("prompt_tokens") or 0), int(d.get("completion_tokens") or 0)
            c = run_cost(pt, ct)
            ts = str(d.get("ts") or "")
            runs += 1
            cost += c
            totals["prompt_tokens"] += pt
            totals["completion_tokens"] += ct
            if d.get("error"):
                totals["errors"] += 1
            if pt > 2_000_000:
                totals["sweeps"] += 1
            elif pt > 100_000:
                totals["mail"] += 1
            if ts[:7] == month and ts[:10]:
                by_day[ts[:10]] = by_day.get(ts[:10], 0.0) + c
    return {"runs": runs, "cost": cost, "by_day": by_day, **totals}


def usage_for(slug: str, month: str | None = None, plan: str | None = None,
              cfg_path: pathlib.Path | None = None) -> dict:
    """Measured spend for ONE ACCOUNT: lifetime totals plus this month's window.

    Sources, first that has data wins: the tenant's own ledger (`<workspace>/data/usage.jsonl`, appended
    by gates/model_budget.py after every run - it is the file the budget gate enforces against, so it is
    the number the subscriber must see here), the per-host meter (`usage/<slug>.jsonl`, written by a
    managed deployment), then the engine's own per-run audit (a self-hosted install has only that). The
    monthly figures are what the plan allowance is measured against, so they are reported separately
    instead of being folded into the lifetime totals.
    """
    month = month or _now_month()
    cfg_path = pathlib.Path(cfg_path) if cfg_path else ROOT / "config" / "tenant.yaml"
    try:
        cfg = tenant_cfg(cfg_path) or {}
    except Exception:
        cfg = {}
    keys = ("runs", "cost", "prompt_tokens", "completion_tokens", "errors", "sweeps", "mail")
    totals = {k: 0 for k in keys}
    totals["cost"] = 0.0
    m = dict(totals, undated=0)

    def absorb(f: pathlib.Path) -> int:
        """Add one usage file to the lifetime totals and to this month's window. Returns lines read."""
        if not f.exists():
            return 0
        used = 0
        for line in f.read_text(errors="replace", encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            pt, ct = int(d.get("prompt_tokens", 0)), int(d.get("completion_tokens", 0))
            cost = run_cost(pt, ct)
            bucket = "sweeps" if pt > 2_000_000 else ("mail" if pt > 100_000 else "")
            ts = str(d.get("ts", ""))
            in_month = bool(ts) and ts[:7] == month
            # a line may aggregate several runs (a backfill or a merged meter): the plan allowance is
            # measured in RUNS, so the count is what the line says, never one-per-line
            try:
                in_line = max(1, int(d.get("runs") or 1))
            except (TypeError, ValueError):
                in_line = 1
            used += in_line
            for acc in ([totals] + ([m] if in_month else [])):
                acc["runs"] += in_line
                acc["cost"] += cost
                acc["prompt_tokens"] += pt
                acc["completion_tokens"] += ct
                if bucket:
                    acc[bucket] += 1
                if d.get("error"):
                    acc["errors"] += 1
            if not ts:
                m["undated"] += 1
        return used

    ws = ledger = None
    try:
        ws = _workspace(cfg) if cfg else None
        ledger = (ws / "data" / "usage.jsonl") if ws else None
    except Exception:
        ws = ledger = None
    measurement = "this account's own ledger"
    if not (ledger and absorb(ledger)):
        measurement = "the product meter"
        if not absorb(USAGE_DIR / f"{slug}.jsonl"):
            measurement = "nothing recorded yet"

    plan = plan or (cfg.get("billing") or {}).get("plan", "starter")
    entry = plan_entry(plan) or None
    includes = ((entry or {}).get("limits") or {}).get("agent_runs_included_month")
    per_extra = (entry or {}).get("price_usd_per_extra_run", 0.39)
    overage = max(0, m["runs"] - includes) if includes else 0

    # With no ledger and no meter, the engine's own audit is the measurement. Without this the Cost tab of
    # a self-hosted install reads zero while the hunt is spending real money every hour.
    try:
        audit = audit_usage(cfg_path, month)
    except Exception:
        audit = {"runs": 0, "cost": 0.0, "by_day": {}, "prompt_tokens": 0, "completion_tokens": 0,
                 "errors": 0, "sweeps": 0, "mail": 0}
    if not totals["runs"] and audit["runs"]:
        measurement = "the engine's per-run audit"
        month_runs = sum(1 for _ in [audit]) and audit["runs"]
        for k in ("prompt_tokens", "completion_tokens", "errors", "sweeps", "mail"):
            totals[k] = audit[k]
            m[k] = audit[k]
        totals["runs"] = audit["runs"]
        totals["cost"] = audit["cost"]
        m["runs"] = audit["runs"]
        m["cost"] = audit["cost"]
        overage = max(0, m["runs"] - includes) if includes else 0

    totals.update({
        "plan": plan,
        "price_usd_month": (entry or {}).get("price_usd_month"),
        "price_usd_per_extra_run": per_extra,
        "includes_runs": includes,
        "margin_multiple": round(entry["price_usd_month"] / totals["cost"], 2)
        if entry.get("price_usd_month") and totals["cost"] else None,
        "rates": RATES,
        "per_run_cost": round(totals["cost"] / totals["runs"], 4) if totals["runs"] else 0.0,
        "spend": round(totals["cost"], 4),
        "window": month,
        "plan_limits": (entry or {}).get("limits") or {},
        "runs_remaining": max(0, includes - m["runs"]) if includes else None,
        "measurement_source": measurement,
        "spend_by_day": {k: round(v, 4) for k, v in sorted(audit["by_day"].items())},
        # The account's budget dial and today's spend, from the gate that enforces it - one source for the
        # gate, the Cost panel and the Alerts view, so a subscriber can never be shown a different number
        # from the one their volume was decided by.
        "budget": budget_state_for(ws, cfg),
        "this_month": dict(m, cost=round(m["cost"], 4),
                           per_run_cost=round(m["cost"] / m["runs"], 4) if m["runs"] else 0.0,
                           runs_remaining=max(0, includes - m["runs"]) if includes else None,
                           overage_runs=overage,
                           overage_cost=round(overage * float(per_extra or 0), 2),
                           spend=round(m["cost"], 4),
                           includes_runs=includes),
    })
    return totals


def budget_state_for(ws: pathlib.Path | None, cfg: dict | None) -> dict | None:
    """Today's model spend and the account's budget dial, from the gate that enforces both.

    None when the gate is not on this host: the Cost panel then simply does not claim a budget it cannot
    enforce. A broken dial is the gate's problem to report (`degraded`), never this panel's to crash on.
    """
    if _model_budget is None:
        return None
    try:
        return _model_budget.state(workspace=str(ws) if ws else "", cfg=cfg or {})
    except Exception as exc:  # a broken dial must not take the Cost panel down with it
        print(f"model budget unavailable: {exc}", file=sys.stderr)
        return None


def notifier_for(cfg_path: pathlib.Path, dry_run: bool = False):
    """Build a Notifier for the tenant, or raise with a readable reason."""
    from notify import Notifier  # type: ignore  # engine/notify/notify.py
    cfg = tenant_cfg(cfg_path)
    ws = workspace_for(cfg) if cfg.get("tenant", {}).get("slug") else ROOT / "hunts" / "unknown"
    return Notifier(cfg, ws, dry_run=dry_run), cfg


def notify_summary(cfg_path: pathlib.Path) -> dict:
    """Config summary for the UI. Salts nothing: describe() already refuses to echo secrets."""
    try:
        n, cfg = notifier_for(cfg_path)
        out = n.describe()
    except Exception as e:
        return {"error": str(e)[:200], "channels": []}
    # the app's own environment may hold a token file rather than an env var
    tg = (cfg.get("delivery") or {}).get("notifications", {}).get("telegram", {}) or {}
    tf = tg.get("token_file")
    if tf:
        p = pathlib.Path(tf).expanduser()
        out["telegram"]["token_file"] = str(p)
        out["telegram"]["token_present"] = out["telegram"]["token_present"] or p.exists()
    em = (cfg.get("delivery") or {}).get("notifications", {}).get("email", {}) or {}
    out["email"]["send_pdf_attachments"] = bool(em.get("send_pdf_attachments", True))
    out["thresholds"] = list(((cfg.get("delivery") or {}).get("notifications") or {}).get("ping_on") or [])
    out["recent"] = n.ledger.records()[-5:]
    return out


def job_states(profile: str) -> tuple[list[dict], str]:
    """Ask the scheduler for this profile's jobs. Returns (jobs, error_reason).

    The error is reported instead of swallowing it: an empty job list because hermes is missing
    looks exactly like an empty job list because the tenant has no jobs, and the customer deserves
    to know which one it is.
    """
    binary = hermes_bin()
    if not binary:
        return [], "the scheduler CLI (hermes) is not on this host's PATH"
    cmd = [binary] + (["-p", profile] if profile != "default" else []) + ["cron", "list", "--all"]
    r = run_command(cmd, timeout=30)
    jobs, cur = [], {}

    def flush():
        if cur:
            jobs.append(dict(cur))

    for line in r["out"].splitlines():
        line = line.rstrip()
        stripped = line.strip()
        if HEX12.match(stripped):
            flush()
            cur.clear()
            cur.update({"id": stripped.split()[0], "state": stripped.split("[")[1].rstrip("]")})
        elif ":" in stripped and cur:
            key, _, value = stripped.partition(":")
            key, value = key.strip().lower().replace(" ", "_"), value.strip()
            if key == "name":
                cur["name"] = value
            elif key == "schedule":
                cur["schedule"] = value
            elif key == "next_run":
                cur["next_run"] = value
            elif key == "last_run":
                parts = re.split(r"\s{2,}", value, maxsplit=1)
                cur["last_run"] = parts[0].strip()
                cur["last_outcome"] = (parts[1].strip() if len(parts) > 1 else "unknown")
            elif key == "dispatch":
                cur["dispatch"] = value
            elif key == "execution":
                cur["execution"] = value
            elif key in ("script", "mode", "deliver", "repeat"):
                cur[key] = value
    flush()
    if not jobs and not r["ok"]:
        return [], f"cron list failed (rc={r['rc']}): {r['tail']}"
    return jobs, ""


def tenant_job_names(cfg: dict, jobs: list[dict]) -> list[str]:
    """Only this tenant's own jobs: the sweep/mail/backup/sheets set is named `<slug>-*`."""
    slug = str((cfg.get("tenant") or {}).get("slug", "") or "")
    prefix = f"{slug}-"
    return [j["name"] for j in jobs if j.get("name", "").startswith(prefix)]


def sweep_job_name(cfg: dict) -> str:
    return SWEEP_JOB.format(slug=(cfg.get("tenant") or {}).get("slug", ""))


def sheets_job_name(cfg: dict, jobs: list[dict] | None = None) -> str:
    """This tenant's sheets job, resolved against the real job list.

    The live host names it <slug>-tracker-sheets-sync and the provisioned template ships
    <slug>-sheets-sync, so a name that matches neither is reported rather than silently queuing
    nothing.
    """
    slug = str((cfg.get("tenant") or {}).get("slug", "") or "")
    candidates = [SHEET_JOB.format(slug=slug)] + [a.format(slug=slug) for a in SHEET_JOB_ALIASES]
    names = {j.get("name") for j in (jobs or [])}
    for cand in candidates:
        if cand in names:
            return cand
    return candidates[0]


def hunt_summary(cfg: dict, jobs: list[dict], error: str) -> dict:
    """Is the hunt live? Per-job cadence plus the last real outcome, or the reason we cannot say.

    Counted over this tenant's own jobs: another tenant's job on the same host must not make this
    customer's hunt look live.
    """
    mine = [j for j in jobs if j.get("name", "") in tenant_job_names(cfg, jobs)] or jobs
    active = [j for j in mine if j.get("state") in ("active", "running")]
    return {
        "live": bool(active),
        "jobs_active": len(active),
        "jobs_total": len(mine),
        "jobs_on_host": len(jobs),
        "jobs_error": error,
        "sweep_job": sweep_job_name(cfg),
        "jobs": [{k: j.get(k, "") for k in ("id", "name", "state", "schedule", "next_run",
                                            "last_run", "last_outcome", "dispatch", "script")}
                 for j in mine],
    }


def action_row() -> list[dict]:
    """The one obvious action row. Every entry names its method and whether it needs the token."""
    return [
        {"id": "sweep", "label": "Run a sweep now", "method": "POST", "url": "/api/control/sweep",
         "token_required": True, "hint": "queues the sweep job on the scheduler's next tick"},
        {"id": "pause", "label": "Pause the hunt", "method": "POST", "url": "/api/control/pause",
         "token_required": True, "hint": "pauses every scheduled job for this tenant"},
        {"id": "resume", "label": "Resume the hunt", "method": "POST", "url": "/api/control/resume",
         "token_required": True, "hint": "resumes them again"},
        {"id": "alert-test", "label": "Send a test alert", "method": "POST",
         "url": "/api/control/alert-test", "token_required": True,
         "hint": "sends one alert through every enabled channel"},
        {"id": "sheet-sync", "label": "Sync the sheet now", "method": "POST",
         "url": "/api/control/sheet-sync", "token_required": True,
         "hint": "runs this tenant's sheets job: the row store is pushed to the Google Sheet"},
        {"id": "billing", "label": "Plan and billing", "method": "GET", "url": "/api/billing",
         "token_required": False, "hint": "plan, licence state and how to get an invoice"},
    ]


def sheet_status(cfg: dict, ws: pathlib.Path, rows: list[dict] | None = None) -> dict:
    """What this candidate's Google Sheet holds: row counts, sheet id, last push.

    Read from the export payload the sync writes and from the sync stamp, never from a workbook.
    The tracker is the sheet, the row store is its source, and the xlsx is a derived CV render
    under output/ that nobody reads.
    """
    slug = str((cfg.get("tenant") or {}).get("slug", "") or "")
    state = ws / "data" / "ops"
    out = {"rows": "", "data_rows": "", "row_store": "", "sheet_id": "", "sheet_url": "",
           "last_push_utc": "", "in_sync": None}
    payload = None
    for cand in (state / "tracker_export.json",
                 pathlib.Path(f"/tmp/tracker_export_{slug}.json")):
        try:
            if cand.is_file():
                payload = json.loads(cand.read_text(encoding="utf-8"))
                break
        except Exception:
            payload = None
    row = (payload or {}).get(slug) if isinstance(payload, dict) else None
    if isinstance(row, dict) and isinstance(row.get("rows"), list) and row["rows"]:
        out["rows"] = len(row["rows"])                  # includes the header row
        out["data_rows"] = len(row["rows"]) - 1
        out["row_store"] = str(row.get("row_store", "") or "")
    for cand in (pathlib.Path.home() / ".hermes" / "profiles" / slug / "tracker_sheets.json",
                 pathlib.Path.home() / ".hermes" / "tracker_sheets.json"):
        try:
            if cand.is_file():
                sid = (json.loads(cand.read_text(encoding="utf-8")) or {}).get(slug)
                if sid:
                    out["sheet_id"] = str(sid)
                    out["sheet_url"] = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
                    break
        except Exception:
            continue
    try:
        out["last_push_utc"] = str(json.loads((state / "sheets_sync_stamp.json").read_text(encoding="utf-8"))
                                   .get("utc", ""))
    except Exception:
        pass
    local = len(rows or [])
    if out["data_rows"] != "":
        out["in_sync"] = int(out["data_rows"]) == local
    return out


def health(cfg: dict, ws: pathlib.Path) -> dict:
    errors = validate(cfg)[0] if cfg else ["no tenant config"]
    rows = tracker_rows(ws)
    return {"config_valid": not errors, "config_errors": errors[:5], "workspace": str(ws),
            "row_store_present": (ws / "build_tracker.py").exists(),
            "rows": len(rows), "sheet": sheet_status(cfg, ws, rows)}


def _workspace(cfg: dict) -> pathlib.Path:
    try:
        return workspace_for(cfg) if cfg.get("tenant", {}).get("slug") else ROOT / "hunts" / "unknown"
    except Exception:
        return ROOT / "hunts" / "unknown"


def state(cfg_path: pathlib.Path) -> dict:
    try:
        cfg = tenant_cfg(cfg_path) or {}
    except Exception:
        cfg = {}
    ws = _workspace(cfg)
    rows = tracker_rows(ws)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    recent = sort_rows(rows)[:25]
    slug = (cfg.get("tenant") or {}).get("slug", "unknown")
    plan = (cfg.get("billing") or {}).get("plan", "starter")
    dials = {
        "countries": (cfg.get("targeting") or {}).get("countries", {}),
        "primary_share": ((cfg.get("targeting") or {}).get("effort_split") or {}).get("primary_share", 0.8),
        "roles": (cfg.get("targeting") or {}).get("roles", []),
        "salary": cfg.get("salary", {}),
        "schedule": cfg.get("schedule", {}),
    }
    jobs, jobs_error = job_states(profile_for(cfg))
    return {
        "tenant": {"slug": slug, "name": (cfg.get("tenant") or {}).get("display_name", slug),
                   "city": (cfg.get("candidate") or {}).get("city", ""),
                   "email_masked": _mask((cfg.get("candidate") or {}).get("email", ""))},
        "dials": dials,
        "plan": plan,
        "counts": counts,
        "total_rows": len(rows),
        "recent": [{k: r[k] for k in ("id", "company", "role", "location", "status", "fit", "apply_url")}
                   for r in recent],
        "usage": usage_for(slug, plan=plan, cfg_path=cfg_path),
        "jobs": jobs,
        "jobs_error": jobs_error,
        "hunt": hunt_summary(cfg, jobs, jobs_error),
        "applications": application_stats(rows),
        "actions": action_row(),
        "health": health(cfg, ws),
    }


def overview(cfg_path: pathlib.Path) -> dict:
    """The overview panel: is the hunt live, what did it do last, what is in the tracker."""
    cfg = tenant_cfg(cfg_path) or {}
    ws = _workspace(cfg)
    rows = tracker_rows(ws)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    ordered = {s: counts[s] for s in STATUS_ORDER if s in counts}
    ordered.update({k: v for k, v in sorted(counts.items()) if k not in ordered})
    jobs, jobs_error = job_states(profile_for(cfg))
    slug = (cfg.get("tenant") or {}).get("slug", "unknown")
    plan = (cfg.get("billing") or {}).get("plan", "starter")
    return {
        "tenant": {"slug": slug, "name": (cfg.get("tenant") or {}).get("display_name", slug)},
        "hunt": hunt_summary(cfg, jobs, jobs_error),
        "counts": ordered,
        "counts_other": {k: v for k, v in counts.items() if k not in ordered},
        "total_rows": len(rows),
        "applications": application_stats(rows),
        "usage": usage_for(slug, plan=plan, cfg_path=cfg_path),
        "actions": action_row(),
        "health": health(cfg, ws),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# --------------------------------------------------------------------------- alerts and documents
def _pack_slug(row) -> str:
    """The application's folder name: recorded in the row's notes when the pack was written."""
    notes = str(row.get("notes") or "")
    m = re.search(r"pack:\s*(applications/[\w./-]+)", notes)
    if m:
        return m.group(1).split("/")[-1]
    src = f"{row.get('company', '')} {row.get('role', '')} {row.get('apply_url', '')}".lower()
    m = re.search(r"/([a-z0-9-]{4,})/?(?:\?|$)", str(row.get("apply_url") or ""))
    slug = re.sub(r"[^a-z0-9]+", "-", f"{row.get('company', '')}-{row.get('role', '')}".lower()).strip("-")
    return (slug[:60] or m.group(1) if m else slug[:60])


def pack_docs(ws: pathlib.Path, slug: str) -> list:
    """The documents this application actually generated, with their sizes."""
    if not slug:
        return []
    d = ws / "applications" / slug
    if not d.is_dir() or d.is_symlink():
        return []
    wanted = (("cv.pdf", "Tailored CV", "pdf"), ("cover-letter.pdf", "Cover letter", "pdf"),
              ("jd.md", "Job description", "md"), ("fit.md", "Fit assessment", "md"),
              ("email-to-hr.md", "Application email", "md"), ("tailoring.json", "Tailoring record", "json"))
    out = []
    for name, label, kind in wanted:
        f = d / name
        if f.is_file() and f.stat().st_size:
            out.append({"name": name, "label": label, "kind": kind, "bytes": f.stat().st_size,
                        "url": f"/api/packs/{slug}/{name}"})
    return out


def alerts_payload(cfg_path: pathlib.Path) -> dict:
    """What needs the candidate, and what does not.

    Alerts are interview invitations and offers - the two statuses the mailbox job promotes from real mail -
    each carrying the documents its pack holds (the CV that was sent, the job description, and the invitation
    the mail job filed). Rejections and receipts are the quiet side: counted, listed, and never raised as an
    alert, because a rejection needs no action and a receipt is not news.
    """
    cfg = tenant_cfg(cfg_path)
    ws = _workspace(cfg)
    rows = tracker_rows(ws)
    project = _workspace(cfg)

    def entry(row):
        slug = _pack_slug(row)
        dates = iso_dates(row.get("notes"))
        return {
            "id": row.get("id"), "company": row.get("company"), "role": row.get("role"),
            "status": row.get("status"), "location": row.get("location"),
            "fit": row.get("fit"), "slug": slug,
            "url": row.get("apply_url") or "",
            "last_date": dates[-1] if dates else "",
            "notes": str(row.get("notes") or "")[:400],
            "docs": pack_docs(project, slug),
        }

    alerts = [entry(r) for r in rows if str(r.get("status")) in ALERT_STATUSES]
    alerts.sort(key=lambda a: (a["status"] != "Offer", a["last_date"]))
    muted = [entry(r) for r in rows if str(r.get("status")) == "Rejected"]
    muted.sort(key=lambda a: a["last_date"], reverse=True)
    receipts = [entry(r) for r in rows if str(r.get("status")) == "Submitted"]
    receipts.sort(key=lambda a: a["last_date"], reverse=True)

    # Invitations the mailbox job filed and delivered: the notify ledger records every send with its
    # attachments, so the alerts view can link the invitation file the mail job created.
    invitations = []
    led = _profile_dir(cfg_path) / "workspace" / "data" / "notify-ledger.jsonl"
    if led.is_file():
        for line in led.read_text(errors="replace", encoding="utf-8").splitlines()[-40:]:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("attachments") and d.get("ok"):
                invitations.append({"ts": str(d.get("ts"))[:16], "channel": d.get("channel"),
                                    "files": d.get("attachments"), "key": str(d.get("key"))[:120]})
    invitations.reverse()
    # The interview backoff, stated rather than applied in silence. It reads the same rows the alerts do, so
    # the count a reader sees here is exactly the count that reduced the cap.
    backoff = {"enabled": False, "active": False, "line": "", "rate": 0, "pending": [], "pending_count": 0}
    try:
        import interview_backoff

        dial = ((cfg.get("targeting") or {}).get("interview_backoff") or {})
        backoff = interview_backoff.state(rows, enabled=dial.get("enabled", True),
                                          rate=dial.get("rate", interview_backoff.DEFAULT_RATE))
    except Exception as exc:  # a broken dial must not take the alerts view down with it
        print(f"interview backoff unavailable: {exc}", file=sys.stderr)

    # The account's model budget, beside the backoff and by the same rule: the subscriber pays for this
    # spend, so a sweep that was slowed or stopped by it says so here, with today's figure and the dial
    # that produced it. Silence would read as the tool having broken.
    budget = budget_state_for(project, cfg)

    return {"backoff": backoff, "budget": budget, "alerts": alerts, "muted": muted[:40],
            "receipts": receipts[:40],
            "invitations": invitations[:20],
            "counts": {"alerts": len(alerts), "muted": len(muted), "receipts": len(receipts)}}


def public_app_dir() -> pathlib.Path:
    return APP_DIR


def _app_asset(name: str):
    """A file inside dashboard/app, or None. Never leaves that directory."""
    if not name or "/" in name.strip("/") or name.startswith("."):
        return None
    base = APP_DIR.resolve()
    f = (base / name).resolve()
    if base not in f.parents or not f.is_file():
        return None
    return f


def _oauth_client() -> tuple:
    """(client_id, client_secret, source) from the deployment's own client secret file."""
    configured = os.environ.get("GOOGLE_CLIENT_SECRET_FILE", "").strip()
    candidates = [pathlib.Path(configured).expanduser()] if configured else []
    candidates += [HOST_HOME / "google_client_secret.json",
                   _profile_dir(ROOT / "config" / "tenant.yaml") / "google_client_secret.json"]
    for p in candidates:
        if not p.is_file():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        blk = d.get("web") or d.get("installed") or d
        cid, sec = str(blk.get("client_id") or ""), str(blk.get("client_secret") or "")
        if cid and sec:
            return (cid, sec, str(p))
    return ("", "", "")


def auth_status(cfg_path: pathlib.Path) -> dict:
    cfg = tenant_cfg(cfg_path)
    profile = _profile_dir(cfg_path)
    tok = profile / "google_token.json"
    scopes, email = [], ""
    if tok.is_file():
        try:
            d = json.loads(tok.read_text(encoding="utf-8"))
            scopes = [str(x) for x in (d.get("scopes") or [])]
            email = str(d.get("account") or d.get("email") or "")
        except Exception:
            pass
    cid, _sec, src = _oauth_client()
    wanted = [x[0] for x in SIGN_IN_SCOPES]
    return {
        "connected": bool(tok.is_file() and scopes),
        "token_path": str(tok),
        "granted": scopes,
        "missing": [w for w in wanted if w not in scopes],
        "email": email,
        "client_configured": bool(cid),
        "client_id_tail": cid[-24:] if cid else "",
        "client_source": src,
        "can_revoke_at": "https://myaccount.google.com/permissions",
        "permissions": [{"scope": sc, "service": svc, "why": why} for sc, svc, why in SIGN_IN_SCOPES],
    }


# --------------------------------------------------------------------------- Google sign-in
class _StateStore:
    """Pending sign-in attempts. Short-lived, single-use, and in memory: a restart invalidates them, which is
    the safe direction - a stale state must never authorise a token write."""

    TTL_SECONDS = 900

    def __init__(self):
        self._items = {}

    def issue(self) -> str:
        import secrets

        state = secrets.token_urlsafe(24)
        self._items[state] = time.time()
        self._prune()
        return state

    def check(self, state: str) -> bool:
        issued = self._items.pop(state, None)
        self._prune()
        return bool(issued) and (time.time() - issued) < self.TTL_SECONDS

    def _prune(self):
        cutoff = time.time() - self.TTL_SECONDS
        for k in [k for k, v in self._items.items() if v < cutoff]:
            self._items.pop(k, None)


_STATE = _StateStore()


def _redirect_uri(handler) -> str:
    """Where Google sends the code back: this deployment's own callback, never the app's page."""
    host = handler.headers.get("Host", "127.0.0.1:8787")
    proto = handler.headers.get("X-Forwarded-Proto", "")
    if not proto:
        proto = "http" if host.startswith(("127.0.0.1", "localhost", "[::1]")) else "https"
    return f"{proto}://{host}/auth/callback"


def _auth_stub() -> dict:
    """Canned Google responses for tests, and only for tests. Empty unless JHA_AUTH_STUB names a file."""
    path = os.environ.get("JHA_AUTH_STUB", "").strip()
    if not path:
        return {}
    if os.environ.get("DASHBOARD_TOKEN") and os.environ.get("JHA_BOUND_HOST", "") not in ("",
                                                                                           "127.0.0.1",
                                                                                           "localhost"):
        return {}
    try:
        data = json.loads(pathlib.Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _stubbed_exchange(stub):
    def exchange(code, client_id, client_secret, redirect_uri):
        token = (stub.get("tokens") or {}).get(code)
        if token is None:
            raise RuntimeError(f"the auth stub has no token for code {code!r}")
        return token
    return exchange


def _stubbed_userinfo(stub):
    def userinfo(access_token):
        who = (stub.get("users") or {}).get(access_token)
        if who is None:
            raise RuntimeError(f"the auth stub has no user for token {access_token!r}")
        return who
    return userinfo


def auth_start(handler) -> dict:
    cid, _sec, src = _oauth_client()
    if not cid:
        return {"ok": False,
                "error": "no Google client secret on this host: put the OAuth client's JSON at "
                         f"{HOST_HOME / 'google_client_secret.json'} to enable sign-in",
                "permissions": [{"scope": sc, "service": svc, "why": why} for sc, svc, why in SIGN_IN_SCOPES]}
    state = _STATE.issue()
    params = {
        "client_id": cid,
        "redirect_uri": _redirect_uri(handler),
        "response_type": "code",
        "scope": " ".join(sc for sc, _svc, _why in SIGN_IN_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
    return {"ok": True, "url": url, "state": state, "redirect_uri": params["redirect_uri"],
            "client_source": src,
            "permissions": [{"scope": sc, "service": svc, "why": why} for sc, svc, why in SIGN_IN_SCOPES]}


def auth_exchange(code: str, host: str, state: str) -> tuple:
    """Trade the code for a token and store it on the tenant's profile. Returns (ok, message)."""
    cid, sec, _src = _oauth_client()
    if not cid or not sec:
        return (False, "this host has no Google OAuth client configured, so the code cannot be exchanged")
    proto = "http" if host.startswith(("127.0.0.1", "localhost", "[::1]")) else "https"
    body = urllib.parse.urlencode({
        "code": code, "client_id": cid, "client_secret": sec, "grant_type": "authorization_code",
        "redirect_uri": f"{proto}://{host}/auth/callback",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        return (False, f"Google refused the exchange (HTTP {exc.code}). {detail}")
    except Exception as exc:
        return (False, f"could not reach Google to exchange the code: {exc}")

    profile = _profile_dir(ROOT / "config" / "tenant.yaml")
    tok_path = profile / "google_token.json"
    existing = {}
    if tok_path.is_file():
        try:
            existing = json.loads(tok_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    # Never lose a refresh token: Google returns one only on the first consent for a client.
    refresh = payload.get("refresh_token") or existing.get("refresh_token")
    granted = str(payload.get("scope") or "").split()
    token = {
        "access_token": payload.get("access_token", ""),
        "refresh_token": refresh,
        "token_type": payload.get("token_type", "Bearer"),
        "expires_at": time.time() + float(payload.get("expires_in") or 3600),
        "scopes": granted or existing.get("scopes") or [],
        "client_id": cid,
    }
    try:
        tok_path.parent.mkdir(parents=True, exist_ok=True)
        tok_path.write_text(json.dumps(token, indent=1), encoding="utf-8")
        tok_path.chmod(0o600)
    except OSError as exc:
        return (False, f"the token could not be written to {tok_path}: {exc}")
    missing = [sc for sc, _svc, _why in SIGN_IN_SCOPES if sc not in token["scopes"]]
    note = ("All three permissions were granted." if not missing
            else f"Granted, but these were not returned: {', '.join(missing)}")
    return (True, f"{note} The tracker, alerts and cost views read from your own account.")


# --------------------------------------------------------------------------- published snapshot (viewer mode)
# A viewer instance serves a snapshot pushed by the deployment that owns the data. It has no workspace, no
# tokens and no write path: see deploy/snapshot.py on the pushing side.
SNAPSHOT_MAX_BYTES = 120 * 1024 * 1024


def snapshot_path() -> pathlib.Path | None:
    """Where this instance keeps the snapshot, or None when it is not a viewer."""
    env = os.environ.get("JHA_SNAPSHOT", "").strip()
    if env:
        return pathlib.Path(env).expanduser()
    default = ROOT / "config" / "snapshot.json"
    return default if default.is_file() else None


def snapshot_load() -> dict | None:
    p = snapshot_path()
    if p is None or not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def snapshot_age_seconds(snap: dict) -> float | None:
    """How old the published snapshot is. A stale view must be visible as stale, not mistaken for live."""
    import datetime as _dt

    stamp = str(snap.get("generated_at") or "")
    try:
        when = _dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=_dt.timezone.utc)
    return max(0.0, (_dt.datetime.now(_dt.timezone.utc) - when).total_seconds())


def snapshot_routes(snap: dict) -> dict:
    """The read routes a viewer answers, built from the snapshot alone."""
    routes = dict(snap.get("routes") or {})
    apps = snap.get("applications") or {}
    if apps:
        routes["/api/applications"] = apps
    return routes


def snapshot_document(snap: dict, slug: str, name: str):
    """(bytes, content-type) for one snapshotted document, or None."""
    docs = (snap.get("documents") or {}).get(slug) or {}
    entry = docs.get(name)
    if not isinstance(entry, dict) or not entry.get("b64"):
        return None
    import base64 as _b64

    try:
        raw = _b64.b64decode(entry["b64"])
    except Exception:
        return None
    return raw, str(entry.get("ctype") or "application/octet-stream")


def _mask(email: str) -> str:
    if "@" not in email:
        return ""
    user, _, domain = email.partition("@")
    return (user[:2] + "*" * max(1, len(user) - 2) + "@" + domain)


# ---------------------------------------------------------------- billing
def licence_state(cfg: dict, secret: str | None = None) -> dict:
    """What the licence is, never what it says: presence, validity, expiry. The key never leaves here."""
    key = str(((cfg.get("billing") or {}).get("license_key") or "")).strip()
    out = {"present": bool(key), "valid": False, "checked": False, "verified": False,
           "reason": "no licence key in the tenant config (trial or self-hosted)", "plan": "",
           "expires": "", "days_left": None, "runs": None}
    if not key:
        return out
    secret = os.environ.get("LICENCE_SECRET", "") if secret is None else secret
    try:
        ok, reason, payload = _license_module().verify(key, secret=secret)
    except Exception as e:
        return dict(out, reason=f"could not check the licence: {e}", checked=False)
    return dict(out, valid=bool(ok), checked=True, verified=bool(secret), reason=reason,
                plan=str(payload.get("p") or ""), expires=_iso_date(payload.get("e")),
                days_left=_days_left(payload.get("e")), runs=payload.get("r"))


def billing_state(cfg_path: pathlib.Path) -> dict:
    """Plan, licence state, the checkout link and how an invoice is obtained."""
    cfg = tenant_cfg(cfg_path) or {}
    slug = str((cfg.get("tenant") or {}).get("slug", "") or "")
    plan = (cfg.get("billing") or {}).get("plan", "starter")
    doc = pricing_doc()
    policy = doc.get("policy") or {}
    entry = plan_entry(plan) or {}
    billing = cfg.get("billing") or {}
    checkout_url = str(billing.get("checkout_url") or "")
    portal_url = str(billing.get("portal_url") or "")
    command = (f"python3 billing/stripe_checkout.py --tenant {slug or '<slug>'} --plan {plan} "
               f"--success-url <return-url> --cancel-url <cancel-url>")
    return {
        "plan": plan,
        "plan_name": entry.get("name", plan),
        "positioning": entry.get("positioning", ""),
        "price_usd_month": entry.get("price_usd_month"),
        "price_usd_year": entry.get("price_usd_year"),
        "price_usd_per_extra_run": entry.get("price_usd_per_extra_run"),
        "includes": entry.get("includes", []),
        "limits": entry.get("limits", {}),
        "currency": policy.get("currency", "USD"),
        "billing_period": policy.get("billing_period", "month"),
        "trial_days": policy.get("trial_days", 7),
        "plans": [{"id": p["id"], "name": p.get("name"), "price_usd_month": p.get("price_usd_month"),
                   "price_usd_year": p.get("price_usd_year"), "limits": p.get("limits", {})}
                  for p in doc.get("plans", [])],
        "licence": licence_state(cfg),
        "checkout": {
            "configured": bool(checkout_url),
            "url": checkout_url,
            "mode": "subscription",
            "trial_days": policy.get("trial_days", 7),
            "stripe_key_present": bool(os.environ.get("STRIPE_SECRET_KEY", "")),
            "how": ("open the Stripe-hosted link below to start or change the subscription; it is a "
                    "subscription Checkout Session, so the card is stored by Stripe, never by us"
                    if checkout_url else
                    "no checkout link is on file. An operator mints one with billing/stripe_checkout.py "
                    "(command below); it needs STRIPE_SECRET_KEY to be set on this host"),
            "command": command,
        },
        "invoices": {
            "portal_url": portal_url,
            "how": ("Stripe emails a receipt for every charge to the billing address on the "
                    "subscription, and the customer portal link below downloads past invoices and "
                    "receipts as PDFs. If no portal link is on file, ask the operator to mint one "
                    "from the Stripe dashboard (Billing > Customer portal) and set billing.portal_url "
                    "in config/tenant.yaml."),
            "command": command,
        },
        "docs": "docs/PRICING.md",
    }


# ---------------------------------------------------------------- configuration dials
def dials_state(cfg_path: pathlib.Path) -> dict:
    """The dials the customer owns, each with the values it accepts, plus what stays operator-only."""
    cfg = tenant_cfg(cfg_path) or {}
    view = cfg_view(cfg)
    plan = (cfg.get("billing") or {}).get("plan", "starter")
    entry = plan_entry(plan) or {}
    limits = entry.get("limits") or {}
    plan_minutes = limits.get("sweep_interval_minutes")
    current = str(view["schedule.sweep"] or "")
    current_minutes = _minutes(current)
    return {
        "tenant": {"slug": (cfg.get("tenant") or {}).get("slug", ""),
                   "name": (cfg.get("tenant") or {}).get("display_name", "")},
        "plan": plan,
        "countries": {"primary": view["countries"]["primary"],
                      "secondary": view["countries"]["secondary"],
                      "rotation": view["countries"]["rotation"],
                      "options": sorted(EU27),
                      "rule": "EU-only: a non-EU country is refused, not warned about"},
        "roles": {"current": view["roles"], "limit": limits.get("max_role_keywords")},
        "salary": view["salary"],
        "cadence": {"current": current, "options": CADENCE_OPTIONS,
                    "plan_allowed": f"every {plan_minutes}m" if plan_minutes else "",
                    "faster_than_plan": bool(plan_minutes and current_minutes
                                             and current_minutes < plan_minutes),
                    "extra_run_price_usd": entry.get("price_usd_per_extra_run", 0.39)},
        "quiet_hours": {"current": view["quiet_hours"], "format": "HH:MM, two entries (start, end)"},
        # the interview backoff: on by default, and the customer's to turn off
        "interview_backoff": {"current": view.get("interview_backoff") or {},
                              "default": {"enabled": True, "rate": 0.4},
                              "rule": "applying less while an interview is pending is stated in the Alerts view"},
        # the model budget: this account's own daily spend limit, and what happens when it is reached
        "budget": {"current": view.get("budget") or {},
                   "default": {"daily_usd": MODEL_BUDGET_DEFAULT_USD, "on_exceed": "warn",
                               "throttle_rate": 0.25},
                   "options": list(MODEL_BUDGET_ACTIONS),
                   "unit": "USD per day, spent on the model. Measured, never estimated",
                   "rule": "the gate is asked before a sweep spends anything; the Alerts view says what "
                           "today cost and the Cost panel shows it against this dial"},
        "alert_thresholds": {"current": view["ping_on"], "options": PING_OPTIONS, "channels": view["channels"]},
        "writable": ["countries", "roles", "salary", "schedule.sweep", "quiet_hours", "ping_on",
                     "interview_backoff", "budget"],
        "operator_only": {
            "delivery.email_read_only": "the engine never sends mail from the candidate's mailbox",
            "billing.plan": "billing changes go through Stripe, not through this page",
            "work_authorization": "permit and sponsorship rules",
            "language_gate": "which local languages are a hard skip",
            "paths": "where the hunt lives on the host",
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def cfg_view(cfg: dict) -> dict:
    g = cfg.get("targeting") or {}
    countries = g.get("countries") or {}
    n = ((cfg.get("delivery") or {}).get("notifications") or {})
    return {
        "budget": dict(cfg.get("budget") or {}),
        "countries": {"primary": list(countries.get("primary") or []),
                      "secondary": list(countries.get("secondary") or []),
                      "rotation": list(countries.get("rotation") or [])},
        "roles": list(g.get("roles") or []),
        "salary": dict(cfg.get("salary") or {}),
        # the interview backoff dial: surfaced so Settings can render it and a save can diff it
        "interview_backoff": dict(((cfg.get("targeting") or {}).get("interview_backoff")) or {}),
        "schedule.sweep": str((cfg.get("schedule") or {}).get("sweep", "") or ""),
        "quiet_hours": list(n.get("quiet_hours") or []),
        "ping_on": list(n.get("ping_on") or []),
        "channels": list(n.get("channels") or ([n["channel"]] if n.get("channel") else [])),
    }


def _minutes(cadence: str) -> int:
    m = re.fullmatch(r"\s*every\s+(\d+)\s*m\s*", str(cadence or ""))
    return int(m.group(1)) if m else 0


def _yaml_list(text: str, key: str, values: list[str]) -> tuple[str, int]:
    """Replace a list in the tenant YAML, inline `key: [..]` or a `- item` block.

    The example config writes countries inline but roles as a block, and a miss here used to be
    reported as a successful edit while nothing changed. Both shapes are handled, and a miss is
    an error the caller has to deal with.
    """
    rendered = "[" + ", ".join(f'"{v}"' for v in values) + "]"
    new, n = re.subn(rf"(?m)^(\s*{key}:\s*)\[.*\]", rf"\g<1>{rendered}", text, count=1)
    if n:
        return new, n
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(rf"^(\s*){re.escape(key)}:\s*(#.*)?$", line)
        if not m:
            continue
        indent = m.group(1)
        end, j = i + 1, i + 1
        while j < len(lines):
            stripped = lines[j].strip()
            if not stripped:
                j += 1
                continue
            deeper = len(lines[j]) - len(lines[j].lstrip()) > len(indent)
            if not (deeper and stripped.startswith("-")):
                break
            end = j + 1
            j += 1
        if end == i + 1:
            return text, 0
        items = [f'{indent}  - "{v}"' if any(c in v for c in ':#"') else f"{indent}  - {v}"
                 for v in values]
        return "\n".join(lines[:i + 1] + items + lines[end:]), 1
    return text, 0


def _set_in_block(text: str, block: str, key: str, value: str) -> tuple[str, int]:
    """Rewrite one scalar inside an anchored YAML block, e.g. the `daily_usd:` of `budget:`.

    Anchored on the block's own indented lines, so a `daily_usd:` anywhere else in the file (or a key of
    the same name under another section) is never touched. A key that is absent from the block is added
    as its first line, keeping the block's indentation - a dial the customer can set is worthless if the
    only way to set it is to already be in the file.
    """
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.fullmatch(rf"\s*{re.escape(block)}:\s*(#.*)?", line):
            start = i
            break
    if start is None:
        return text, 0
    base = len(lines[start]) - len(lines[start].lstrip())
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        if len(line) - len(line.lstrip()) <= base:
            break                     # the block ended
        if re.match(rf"\s*{re.escape(key)}:\s*", line):
            lines[j] = re.sub(rf"^(\s*{re.escape(key)}:\s*).*$", rf"\g<1>{value}", line)
            return "\n".join(lines), 1
    lines.insert(start + 1, " " * (base + 2) + f"{key}: {value}")
    return "\n".join(lines), 1


def _render_edits(text: str, payload: dict, before: dict,
                  plan_minutes: int = 0) -> tuple[str, list[dict], list[str], list[str]]:
    """Pure: turn a payload into the new config text. Writes nothing, so a preview is free.

    A dial is only rewritten when its value actually changes: that keeps an untouched dial whose
    key is absent from a hand-edited config from blocking a change elsewhere. When a dial does
    change and its key cannot be found, that is an error, never a silent success.
    """
    changes: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    def note(field: str, old, new) -> None:
        if new != old:
            changes.append({"field": field, "before": old, "after": new})

    def set_list(key: str, wanted: list[str], field: str, old) -> None:
        if wanted == old:
            return
        nonlocal text
        text, n = _yaml_list(text, key, wanted)
        if not n:
            errors.append(f"{field} is not in the tenant config")
        else:
            note(field, old, wanted)

    countries = payload.get("countries")
    if isinstance(countries, dict):
        tiers = {t: [str(x).strip().upper() for x in (countries.get(t) or []) if str(x).strip()]
                 for t in ("primary", "secondary", "rotation")}
        if not tiers["primary"]:
            errors.append("at least one primary country is required")
        seen: set[str] = set()
        for tier, values in tiers.items():
            dupes = sorted({c for c in values if c in seen})
            if dupes:
                errors.append(f"country {dupes} appears in more than one tier")
            seen.update(values)
        if not errors:
            for tier in ("primary", "secondary", "rotation"):
                set_list(tier, tiers[tier], f"countries.{tier}", before["countries"][tier])
            if not errors:
                note("countries", before["countries"], dict(tiers))

    roles = payload.get("roles")
    if isinstance(roles, list):
        wanted = [str(r).strip() for r in roles if str(r).strip()]
        if not wanted:
            errors.append("at least one role keyword is required")
        else:
            set_list("roles", wanted, "roles", before["roles"])

    salary = payload.get("salary") or {}
    if isinstance(salary, dict):
        new_salary = dict(before["salary"])
        for key in ("current_gross", "target_floor"):
            if key not in salary:
                continue
            try:
                value = int(salary[key])
            except (TypeError, ValueError):
                errors.append(f"salary.{key} must be a whole number")
                continue
            if value <= 0:
                errors.append(f"salary.{key} must be greater than zero")
                continue
            if new_salary.get(key) == value:
                continue
            text, n = re.subn(rf"(?m)^(\s*{key}:\s*)\S+", rf"\g<1>{value}", text)
            if not n:
                errors.append(f"salary.{key} is not in the tenant config")
                continue
            new_salary[key] = value
        if "ask_range" in salary:
            pair = list(salary["ask_range"] or [])
            if len(pair) != 2:
                errors.append("salary.ask_range needs two numbers (ask from, ask to)")
            else:
                try:
                    lo, hi = int(pair[0]), int(pair[1])
                except (TypeError, ValueError):
                    errors.append("salary.ask_range must be two whole numbers")
                else:
                    if lo <= 0 or hi < lo:
                        errors.append("salary.ask_range must be positive and end at or above its start")
                    elif list(new_salary.get("ask_range") or []) != [lo, hi]:
                        text, n = re.subn(r"(?m)^(\s*ask_range:\s*)\[.*\]", rf"\g<1>[{lo}, {hi}]", text)
                        if not n:
                            errors.append("salary.ask_range is not in the tenant config")
                        else:
                            new_salary["ask_range"] = [lo, hi]
        note("salary", before["salary"], new_salary)

    backoff = payload.get("interview_backoff")
    if isinstance(backoff, dict) and "enabled" in backoff:
        wanted = bool(backoff["enabled"])
        was = bool((before.get("interview_backoff") or {}).get("enabled", True))
        if wanted != was:
            # anchored on the interview_backoff block, not on any `enabled:` in the file
            text, n = re.subn(r"(?m)(^\s*interview_backoff:[^\n]*\n\s*enabled:\s*)\S+",
                              lambda m: m.group(1) + ("true" if wanted else "false"), text)
            if not n:
                errors.append("targeting.interview_backoff.enabled is not in the tenant config")
            else:
                note("interview_backoff.enabled", was, wanted)

    budget = payload.get("budget")
    if isinstance(budget, dict):
        was = dict(before.get("budget") or {}) if isinstance(before.get("budget"), dict) else {}
        wanted = dict(was)
        if "daily_usd" in budget:
            try:
                usd = float(budget["daily_usd"])
            except (TypeError, ValueError):
                errors.append("budget.daily_usd must be a number of dollars per day")
            else:
                if usd <= 0 or usd > 10000:
                    errors.append("budget.daily_usd must be above 0 and at most 10000")
                elif usd != float(was.get("daily_usd") or 0):
                    text, n = _set_in_block(text, "budget", "daily_usd", f"{usd:.2f}")
                    if not n:
                        errors.append("budget.daily_usd is not in the tenant config")
                    else:
                        wanted["daily_usd"] = usd
        if "on_exceed" in budget:
            choice = str(budget["on_exceed"] or "").strip().lower()
            if choice not in MODEL_BUDGET_ACTIONS:
                errors.append("budget.on_exceed must be one of " + ", ".join(MODEL_BUDGET_ACTIONS))
            elif choice != str(was.get("on_exceed") or ""):
                text, n = _set_in_block(text, "budget", "on_exceed", choice)
                if not n:
                    errors.append("budget.on_exceed is not in the tenant config")
                else:
                    wanted["on_exceed"] = choice
        if "throttle_rate" in budget:
            try:
                rate = float(budget["throttle_rate"])
            except (TypeError, ValueError):
                errors.append("budget.throttle_rate must be a share between 0 and 1")
            else:
                if not 0 < rate <= 1:
                    errors.append("budget.throttle_rate must be above 0 and at most 1")
                elif rate != float(was.get("throttle_rate") or 0):
                    text, n = _set_in_block(text, "budget", "throttle_rate", f"{rate:g}")
                    if not n:
                        errors.append("budget.throttle_rate is not in the tenant config")
                    else:
                        wanted["throttle_rate"] = rate
        note("budget", was, wanted)

    sweep = payload.get("schedule.sweep")
    if sweep:
        sweep = str(sweep).strip()
        if not re.fullmatch(r"every\s+\d+m", sweep):
            errors.append("cadence must look like 'every 180m'")
        elif sweep != before["schedule.sweep"]:
            text, n = re.subn(r'(?m)^(\s*sweep:\s*)"?[^"\n]*"?', rf'\g<1>"{sweep}"', text)
            if not n:
                errors.append("schedule.sweep is not in the tenant config")
            else:
                note("schedule.sweep", before["schedule.sweep"], sweep)
                minutes = _minutes(sweep)
                if plan_minutes and minutes and minutes < plan_minutes:
                    warnings.append(f"every {minutes}m is faster than the plan's every {plan_minutes}m: "
                                    f"the extra runs are billed at the plan's per-run price")

    quiet = payload.get("quiet_hours")
    if isinstance(quiet, list):
        wanted = [str(x).strip() for x in quiet]
        bad = [x for x in wanted if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", x)]
        if len(wanted) != 2 or bad:
            errors.append("quiet hours must be two times in HH:MM form (start, end)")
        else:
            set_list("quiet_hours", wanted, "quiet_hours", before["quiet_hours"])

    ping = payload.get("ping_on")
    if isinstance(ping, list):
        wanted = [str(x).strip() for x in ping if str(x).strip()]
        if not wanted:
            errors.append("at least one alert threshold must stay on")
        else:
            unknown = [x for x in wanted if x not in PING_OPTIONS]
            if unknown:
                warnings.append(f"thresholds the engine does not document: {unknown} (kept as-is)")
            set_list("ping_on", wanted, "ping_on", before["ping_on"])

    return text, changes, errors, warnings


def config_change(cfg_path: pathlib.Path, payload: dict, write: bool = False) -> tuple[bool, dict]:
    """Preview or apply a dial change. The slow burn: nothing is written until the whole result
    validates, and a rejection leaves the file exactly as it was (byte for byte)."""
    try:
        cfg = tenant_cfg(cfg_path)
    except Exception as e:
        return False, {"ok": False, "refused": True, "errors": [f"could not read the tenant config: {e}"],
                       "warnings": [], "changes": [], "message": f"refused: could not read the config ({e})"}
    if not cfg:
        return False, {"ok": False, "refused": True, "errors": ["no tenant config found"],
                       "warnings": [], "changes": [], "message": "refused: no tenant config found"}
    original = cfg_path.read_text(encoding="utf-8")
    before = cfg_view(cfg)
    plan = str((cfg.get("billing") or {}).get("plan", "starter"))
    plan_minutes = int((((plan_entry(plan) or {}).get("limits") or {})
                        .get("sweep_interval_minutes")) or 0)
    text, changes, errors, warnings = _render_edits(original, payload, before, plan_minutes)
    if not errors:
        try:
            candidate = read_config_minimal(text)
            verrors, vwarnings = validate(candidate)
            errors += verrors
            warnings += vwarnings
            warnings += _cadence_warnings(candidate)
        except Exception as e:
            errors.append(f"the edited config would not parse: {e}")
    result = {
        "ok": not errors,
        "refused": bool(errors),
        "errors": errors,
        "warnings": warnings,
        "changes": changes,
        "written": False,
        "message": ("refused: " + errors[0]) if errors else
                   ("no change: every dial already matches" if not changes else
                    ("applied: " if write else "would apply: ") + ", ".join(c["field"] for c in changes)),
    }
    if errors or not changes or not write:
        return not errors, result

    scope_path = _workspace(cfg) / "eu_scope.json"
    old_scope = scope_path.read_text(encoding="utf-8") if scope_path.exists() else None
    tmp = cfg_path.with_name(cfg_path.name + ".dash-tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        shutil.copymode(cfg_path, tmp)
        os.replace(tmp, cfg_path)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        return False, dict(result, ok=False, refused=True, message=f"refused: could not write the config ({e})")
    try:
        new_cfg = read_config(cfg_path)
        verrors, _ = validate(new_cfg)
        if verrors:
            raise ValueError(verrors[0])
        ok, msg = _sync_workspace(new_cfg)
        if not ok:
            raise ValueError(msg)
    except Exception as e:
        cfg_path.write_text(original, encoding="utf-8")
        # The rollback must not become the failure. If the workspace cannot even be touched (a
        # workspace path under a regular file, or an unwritable one) then looking at the scope file
        # raises ENOTDIR/EACCES, and an unguarded call here would kill the connection with an
        # unhandled OSError instead of answering 400 with the refusal the operator needs to see.
        try:
            if old_scope is None:
                scope_path.unlink(missing_ok=True)
            else:
                scope_path.write_text(old_scope, encoding="utf-8")
        except OSError:
            pass
        return False, dict(result, ok=False, refused=True, written=False,
                           message=f"refused and rolled back: {e}")
    return True, dict(result, written=True, scope=str(scope_path),
                      message="applied: " + ", ".join(c["field"] for c in changes))


def _cadence_warnings(cfg: dict) -> list[str]:
    plan = (cfg.get("billing") or {}).get("plan", "starter")
    floor = (((plan_entry(plan) or {}).get("limits") or {}).get("sweep_interval_minutes")) or 0
    minutes = _minutes(str((cfg.get("schedule") or {}).get("sweep", "")))
    if floor and minutes and minutes < floor:
        return [f"schedule.sweep every {minutes}m is faster than the {plan} plan's every {floor}m: "
                f"extra runs are billed per run"]
    return []


def _sync_workspace(cfg: dict) -> tuple[bool, str]:
    """The workspace files the unattended run reads have to follow the dials.

    Two of them, and both matter for the same reason - the run reads the workspace, not this config file:

      * `eu_scope.json`, or the next sweep would hunt the old countries;
      * the budget block of the workspace's own dial file (notify.json / config.json, the same two names
        engine/notify/apply_email.py reads), or the next sweep would enforce a budget the subscriber has
        since changed - and a spend limit nobody can raise from the interface is a limit that gets
        switched off by hand instead.

    A failure in either is a refusal that rolls the config back: a dial the engine cannot see is worse
    than a change that did not happen.
    """
    try:
        from provisioning.provision_tenant import write_scope
        ws = _workspace(cfg)
        ws.mkdir(parents=True, exist_ok=True)
        write_scope(cfg, ws)
    except Exception as e:
        return False, f"scope regenerate failed: {e}"
    budget = cfg.get("budget")
    if isinstance(budget, dict) and budget:
        if _model_budget is None:
            return False, "the model-budget gate is missing from this checkout"
        try:
            _model_budget.write_budget(ws, daily_usd=budget.get("daily_usd"),
                                       on_exceed=budget.get("on_exceed"),
                                       throttle_rate=budget.get("throttle_rate"))
        except Exception as e:
            return False, f"budget carry failed: {e}"
    return True, ""


def apply_config(cfg_path: pathlib.Path, payload: dict) -> tuple[bool, str]:
    """Backwards-compatible entry point: (ok, message)."""
    ok, result = config_change(cfg_path, payload, write=True)
    return ok, result["message"]


# ---------------------------------------------------------------- controls
def toggle_job(profile: str, name: str, action: str) -> tuple[bool, str]:
    if action not in {"resume", "pause"}:
        return False, "action must be resume or pause"
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", name):
        return False, "bad job name"
    binary = hermes_bin()
    missing = scheduler_missing(binary)
    if missing:
        return False, missing
    cmd = [binary] + (["-p", profile] if profile != "default" else []) + ["cron", action, name]
    r = run_command(cmd, timeout=60)
    return r["ok"], (r["tail"] if r["ok"] else f"cron {action} {name} failed (rc={r['rc']}): {r['tail']}")


def control_toggle(cfg_path: pathlib.Path, action: str, job: str | None = None) -> tuple[bool, str, dict]:
    cfg = tenant_cfg(cfg_path) or {}
    profile = profile_for(cfg)
    jobs, error = job_states(profile)
    if error and not jobs:
        return False, f"could not list the jobs: {error}", {"jobs": [], "error": error}
    names = [job] if job else tenant_job_names(cfg, jobs)
    if not names:
        return False, "no scheduled jobs found for this tenant", {"jobs": []}
    results = {}
    for name in names:
        ok, message = toggle_job(profile, name, action)
        results[name] = {"ok": ok, "message": message}
    failed = [n for n, v in results.items() if not v["ok"]]
    ok = not failed
    if ok:
        message = f"{action}d {len(names)} job(s): " + ", ".join(names)
    else:
        first = results[failed[0]]["message"]
        message = f"{action} failed for {', '.join(failed)}: {first}"
    return ok, message, {"profile": profile, "jobs": results}


def control_sweep(cfg_path: pathlib.Path, job: str | None = None) -> tuple[bool, str, dict]:
    """Queue the sweep through the scheduler's own CLI: the same path a tick would take."""
    cfg = tenant_cfg(cfg_path) or {}
    profile = profile_for(cfg)
    name = job or sweep_job_name(cfg)
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", name or ""):
        return False, "bad job name", {"job": name}
    binary = hermes_bin()
    missing = scheduler_missing(binary)
    if missing:
        return False, missing, {"job": name, "profile": profile}
    cmd = [binary] + (["-p", profile] if profile != "default" else []) + ["cron", "run", name]
    r = run_command(cmd, timeout=60)
    detail = {"job": name, "profile": profile, "rc": r["rc"], "output": r["tail"]}
    if r["ok"]:
        return True, f"queued {name} for the next scheduler tick ({r['tail']})", detail
    return False, f"the scheduler refused to queue {name} (rc={r['rc']}): {r['tail']}", detail


def alert_test(cfg_path: pathlib.Path, payload: dict) -> tuple[bool, str, dict]:
    """Send a self-test through the notifier the engine itself uses."""
    channel = payload.get("channel")
    if channel and channel not in CHANNELS:
        return False, f"unknown channel: {channel}", {"results": {}}
    try:
        n, _cfg = notifier_for(cfg_path, dry_run=bool(payload.get("dry_run")))
        text = payload.get("text") or (f"jobhunt-agent self-test at {time.strftime('%Y-%m-%d %H:%M')}: "
                                       f"this channel works. Nothing to do.")
        res = n.send(f"selftest:{int(time.time())}", text, subject="jobhunt-agent test",
                     channels=[channel] if channel else None)
    except Exception as e:
        return False, f"could not build the notifier: {e}", {"results": {}}
    ok = any(r.get("ok") or r.get("duplicate") for r in res.values())
    failed = {k: (v.get("error") or "failed") for k, v in res.items()
              if not (v.get("ok") or v.get("duplicate"))}
    if ok:
        message = "self-test delivered to " + ", ".join(k for k, v in res.items()
                                                        if v.get("ok") or v.get("duplicate"))
        if failed:
            message += f" (failed: {failed})"
    else:
        message = "self-test failed: " + (", ".join(f"{k}: {v}" for k, v in failed.items()) or "no channel")
    return ok, message, {"results": res}


def switch_channels(cfg_path: pathlib.Path, payload: dict) -> tuple[bool, str, dict]:
    """Rewire the alert channels. Validated in memory first: a refusal changes no file."""
    wanted = [str(c).strip() for c in (payload.get("channels") or []) if str(c).strip()]
    known = set(CHANNELS)
    bad = [c for c in wanted if c not in known]
    if bad:
        return False, f"unknown channels: {bad}", {}
    if not wanted:
        return False, "at least one channel is required", {}
    original = cfg_path.read_text(encoding="utf-8")
    rendered = "[" + ", ".join(wanted) + "]"
    text, n = re.subn(r"(?m)^(\s*)channels:\s*\[[^\]]*\]", rf"\g<1>channels: {rendered}", original, count=1)
    if not n:
        # older configs carry a single `channel:` key: replace it, else insert above it
        text, n = re.subn(r"(?m)^(\s*)channel:\s*\S+", rf"\g<1>channels: {rendered}", original, count=1)
    if not n:
        text, n = re.subn(r"(?m)^(\s*)notifications:\s*$",
                          lambda m: f"{m.group(1)}notifications:\n{m.group(1)}  channels: {rendered}",
                          original, count=1)
    if not n:
        return False, "no notifications block in the tenant config to write channels into", {}
    try:
        candidate = read_config_minimal(text)
        errors, _ = validate(candidate)
        if errors:
            return False, f"rejected: {errors[0]}", {}
    except Exception as e:
        return False, f"rejected: the edited config would not parse ({e})", {}
    tmp = cfg_path.with_name(cfg_path.name + ".dash-tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        shutil.copymode(cfg_path, tmp)
        os.replace(tmp, cfg_path)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        return False, f"could not write the config ({e})", {}
    return True, "alert channels: " + ", ".join(wanted), {"channels": wanted}


def control_sheet_sync(cfg_path: pathlib.Path) -> tuple[bool, str, dict]:
    """Run this tenant's sheets job through the scheduler CLI: the same path a tick would take.

    That job publishes the row store to the candidate's Google Sheet. The dashboard never rebuilds
    a workbook and never writes to the sheet itself, because a row write already pushes the sheet.
    """
    cfg = tenant_cfg(cfg_path) or {}
    jobs, jobs_error = job_states(profile_for(cfg))
    ok, message, detail = control_sweep(cfg_path, sheets_job_name(cfg, jobs))
    detail["jobs_error"] = jobs_error
    return ok, message, detail


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    cfg_path: pathlib.Path = ROOT / "config" / "tenant.yaml"
    token: str = ""
    index: pathlib.Path = ROOT / "dashboard" / "index.html"
    # Set by main(): True when this server is reachable from anywhere but loopback. Reads are open on a private
    # host (the desktop client uses them over loopback) and token-only on a public one.
    public: bool = False
    # Set by main() in multi-tenant mode: resolves a request's session cookie to that user's own tenant.
    tenancy = None
    default_cfg_path: pathlib.Path = ROOT / "config" / "tenant.yaml"

    # ------------------------------------------------------------------ the tenant this request belongs to
    @property
    def cfg_path(self) -> pathlib.Path:
        """The config every read on this request uses.

        Single-tenant: the deployment's own config, exactly as before. Multi-tenant: the signed-in user's own
        config. There is no fallback to another user's paths: an unauthenticated request is refused earlier.
        """
        if Handler.tenancy is not None and Handler.tenancy.mode == "multi":
            tenant = Handler.tenancy.for_request(self.cookie("jha_session"))
            if tenant is not None:
                return tenant.cfg_path
        return Handler.default_cfg_path

    def cookie(self, name: str) -> str:
        raw = self.headers.get("Cookie", "") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return ""

    # -------------------------------------------------- plumbing
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _extras(self) -> tuple[str, ...]:
        """Values that must never appear in a response: the dashboard token, the licence key."""
        extra = [self.token]
        try:
            billing = (tenant_cfg(self.cfg_path) or {}).get("billing") or {}
            extra.append(str(billing.get("license_key") or ""))
        except Exception:
            pass
        return tuple(extra)

    def _json(self, obj, code: int = 200) -> None:
        body = _scrub(json.dumps(obj, indent=1), self._extras()).encode()
        self._send(code, body)

    def _authed(self) -> bool:
        if not self.token:
            return True          # local single-user mode
        return self.headers.get("X-Dashboard-Token", "") == self.token

    def _operator_ok(self) -> bool:
        """Is this the OPERATOR, proven by a configured token?

        Deliberately stricter than `_authed()`: on a host serving many users, "no token configured" must never
        mean "everyone is the operator". Only a token that exists and matches counts.
        """
        return bool(self.token) and self.headers.get("X-Dashboard-Token", "") == self.token

    def _deny(self) -> bool:
        """True when the request must stop: writes need the token, and the refusal is explicit."""
        if self._authed():
            return False
        self._json({"ok": False, "error": "unauthorised: set X-Dashboard-Token"}, 401)
        return True

    def _body(self) -> dict | None:
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except Exception:
            self._json({"ok": False, "error": "bad json"}, 400)
            return None
        return payload if isinstance(payload, dict) else {}

    def _query(self) -> dict:
        return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

    def _cfg(self) -> dict:
        try:
            return tenant_cfg(self.cfg_path) or {}
        except Exception:
            return {}

    # -------------------------------------------------- GET
    def _exposed(self) -> bool:
        """True when this request reached a server that is not loopback-only."""
        if Handler.public:
            return True
        return bool(self.headers.get("X-Forwarded-For") or self.headers.get("X-Real-IP"))

    def _read_gate(self):
        """None to continue, or a response when this request is not allowed to read.

        Multi-tenant: a signed-in session (or the operator token) is required, because the data belongs to a
        user. Single-tenant on loopback: open, so the desktop client keeps working.
        """
        if Handler.tenancy is not None and Handler.tenancy.mode == "multi":
            # These routes ARE the way in: sign in, ask who I am, log out, and the health check. Listed
            # explicitly rather than as "/api/auth*", so a route added later cannot inherit openness.
            if urllib.parse.urlparse(self.path).path in LOGIN_OPEN_ROUTES:
                return None
            # a user's own session, or the operator: nothing else, and no "no token = open" shortcut
            if self._operator_ok():
                return None
            if Handler.tenancy.for_request(self.cookie("jha_session")) is not None:
                return None
            return self._json({"ok": False, "needs_login": True,
                               "error": "sign in to see your own hunt"}, 401)
        if self._authed():
            return None
        if not self._exposed():
            return None
        return self._json({"ok": False,
                           "error": "unauthorised: this deployment is reachable from outside loopback, so "
                                    "every endpoint needs X-Dashboard-Token",
                           "needs_token": True}, 401)

    def _tenant_or_none(self):
        if Handler.tenancy is None or Handler.tenancy.mode != "multi":
            return None
        return Handler.tenancy.for_request(self.cookie("jha_session"))

    def _may_write(self) -> bool:
        """Who may change something.

        Multi-tenant: only the operator token, or a signed-in user writing to their OWN tenant - and there the
        session IS the authorisation, so no token is required. Single-tenant: unchanged, so a local client with
        no token keeps working.
        """
        if Handler.tenancy is not None and Handler.tenancy.mode == "multi":
            return self._operator_ok() or self._tenant_or_none() is not None
        return self._authed()

    def do_GET(self):  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        # A viewer answers every read from its snapshot and holds nothing else. healthz is excluded here and
        # handled below: it must stay open, and it reports the snapshot's age.
        snap = snapshot_load()
        if snap is None and snapshot_path() is not None and path.startswith("/api/") \
                and path != "/api/healthz":
            # Configured as a viewer, no snapshot yet: an empty dashboard would read as "nothing applied to",
            # which is a different claim from "the deployment has not pushed yet".
            return self._json({"ok": False, "mode": "viewer", "waiting": True,
                               "error": "this instance is a published view and has not received a snapshot "
                                        "yet; the deployment pushes one every few minutes"}, 503)
        if snap is not None and path != "/api/healthz":
            # The read gate applies to snapshot data exactly as it does to live data: a public instance serves
            # nothing without the operator token.
            gated = self._read_gate()
            if gated is not None:
                return gated
            if path.startswith("/api/packs/"):
                m = re.fullmatch(r"/api/packs/([A-Za-z0-9._-]{1,80})/([A-Za-z0-9._-]{1,40})", path)
                if not m:
                    return self._json({"ok": False, "error": "no such document"}, 404)
                got = snapshot_document(snap, m.group(1), m.group(2))
                if got is None:
                    return self._json({"ok": False, "error": "no such document in the snapshot"}, 404)
                raw, ctype = got
                return self._send(200, raw, ctype)
            if path == "/api/sync":
                return self._json({"ok": False, "error": "this instance is a viewer"}, 405)
            served = snapshot_routes(snap)
            if path in served:
                return self._json(served[path])
            if path.startswith("/api/"):
                return self._json({"ok": False, "error": "not in the snapshot"}, 404)

        # /api/healthz and the static app stay open: an uptime check must work, and the interface itself holds
        # no data until it fetches it.
        if path.startswith("/api/") and path != "/api/healthz":
            gated = self._read_gate()
            if gated is not None:
                return gated
        if path in ("/", "/index.html"):
            html = self.index.read_bytes() if self.index.exists() else b"<h1>dashboard missing</h1>"
            return self._send(200, html, "text/html; charset=utf-8")
        if path == "/api/healthz":
            snap = snapshot_load()
            body = {"ok": True, "version": _version()}
            if snap is not None:
                age = snapshot_age_seconds(snap)
                body.update({"mode": "viewer", "snapshot_at": snap.get("generated_at"),
                             "snapshot_age_seconds": round(age) if age is not None else None,
                             "snapshot_rows": (snap.get("applications") or {}).get("total")})
            elif snapshot_path() is not None:
                body.update({"mode": "viewer", "snapshot_at": None,
                             "error": "the snapshot file is missing or unreadable"})
            return self._json(body)
        if path == "/api/state":
            return self._json(state(self.cfg_path))
        if path == "/api/overview":
            return self._json(overview(self.cfg_path))
        if path == "/api/applications":
            cfg = self._cfg()
            q = self._query()
            rows = tracker_rows(_workspace(cfg))
            status = q.get("status", "")
            if status and status.lower() != "all":
                rows = [r for r in rows if r["status"].lower() == status.lower()]
            rows = search_rows(rows, q.get("q", ""))
            rows = sort_rows(rows)
            try:
                limit = min(200, max(1, int(q.get("limit", 200))))
            except ValueError:
                limit = 200
            return self._json({"count": len(rows), "total": len(tracker_rows(_workspace(cfg))),
                               "rows": rows[:limit], "search": q.get("q", ""), "status": status})
        m = re.fullmatch(r"/api/applications/([A-Za-z0-9-]{1,16})", path)
        if m:
            rows = [r for r in tracker_rows(_workspace(self._cfg())) if str(r["id"]) == m.group(1)]
            if not rows:
                return self._json({"ok": False, "error": "no such application"}, 404)
            row = rows[0]
            return self._json({"row": row, "key_dates": iso_dates(row.get("notes")),
                               "notes": row.get("notes", ""), "apply_url": row.get("apply_url", "")})
        if path in ("/app", "/app/"):
            f = APP_DIR / "index.html"
            body = f.read_bytes() if f.is_file() else b"<h1>app missing</h1>"
            return self._send(200, body, "text/html; charset=utf-8")
        if path.startswith("/app/"):
            f = _app_asset(path[len("/app/"):])
            if f is None:
                return self._send(404, b"not found", "text/plain")
            ctype = ("text/css" if f.suffix == ".css" else "application/javascript" if f.suffix == ".js"
                     else "image/svg+xml" if f.suffix == ".svg" else "text/html")
            if ctype.startswith("text/") or ctype == "application/javascript":
                ctype += "; charset=utf-8"
            return self._send(200, f.read_bytes(), ctype)
        if path == "/api/alerts":
            return self._json(alerts_payload(self.cfg_path))
        if path == "/api/auth/status":
            return self._json(auth_status(self.cfg_path))
        if path == "/api/auth/start":
            return self._json(auth_start(self))
        if path == "/api/auth/me":
            tenant = self._tenant_or_none()
            if Handler.tenancy is not None and Handler.tenancy.mode == "multi" and tenant is None:
                return self._json({"ok": False, "signed_in": False, "needs_login": True,
                                   "permissions": [{"scope": sc, "service": svc, "why": why}
                                                   for sc, svc, why in SIGN_IN_SCOPES]})
            if tenant is not None:
                scopes = Handler.tenancy.granted_scopes(tenant)
                return self._json({"ok": True, "signed_in": True, "slug": tenant.slug,
                                   "workspace": str(tenant.workspace),
                                   "granted": scopes,
                                   "missing": [sc for sc, _svc, _why in SIGN_IN_SCOPES if sc not in scopes],
                                   "permissions": [{"scope": sc, "service": svc, "why": why}
                                                   for sc, svc, why in SIGN_IN_SCOPES]})
            return self._json(auth_status(self.cfg_path))
        if path == "/api/auth/logout":
            if Handler.tenancy is not None and Handler.tenancy.mode == "multi":
                Handler.tenancy.end_session(self.cookie("jha_session"))
                self.send_response(303)
                self.send_header("Set-Cookie", "jha_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
                self.send_header("Location", "/app/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self._json({"ok": False, "error": "this deployment is not multi-tenant"}, 404)
        if path == "/auth/callback":
            return self._auth_callback()
        m = re.fullmatch(r"/api/packs/([A-Za-z0-9._-]{1,80})/([A-Za-z0-9._-]{1,40})", path)
        if m:
            return self._pack_document(m.group(1), m.group(2))
        if path == "/api/notify":
            return self._json(notify_summary(self.cfg_path))
        if path in ("/api/usage", "/api/cost"):
            cfg = self._cfg()
            slug = (cfg.get("tenant") or {}).get("slug", "unknown")
            return self._json(usage_for(slug, plan=(cfg.get("billing") or {}).get("plan"),
                                       cfg_path=self.cfg_path))
        if path == "/api/billing":
            return self._json(billing_state(self.cfg_path))
        if path == "/api/config/dials":
            return self._json(dials_state(self.cfg_path))
        if path == "/api/config":
            cfg = self._cfg()
            view = cfg_view(cfg)
            return self._json({"dials": view, "operator_only": dials_state(self.cfg_path)["operator_only"]})
        if path == "/api/control":
            return self._json({"actions": action_row(),
                               "note": "every POST needs the X-Dashboard-Token header; reads do not"})
        return self._json({"error": "not found"}, 404)

    # -------------------------------------------------- POST
    # ------------------------------------------------------------------ application documents
    def _pack_document(self, slug: str, name: str):
        """One document from one application's own folder. Slug and name are constrained by the route regex,
        and the resolved path must still sit inside that folder."""
        cfg = self._cfg()
        base = (_workspace(cfg) / "applications").resolve()
        target = (base / slug / name).resolve()
        if base not in target.parents or not target.is_file() or target.stat().st_size == 0:
            return self._json({"ok": False, "error": "no such document"}, 404)
        data = target.read_bytes()
        ctype = {"pdf": "application/pdf", "md": "text/plain; charset=utf-8",
                 "json": "application/json"}.get(target.suffix.lstrip("."), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    # ------------------------------------------------------------------ multi-tenant sign-in
    def _multi_signin(self, code: str, state: str) -> tuple:
        """Exchange the code, identify the person, provision THEIR tenant, then hand back a session cookie."""
        t = Handler.tenancy
        cid, sec, _src = _oauth_client()
        if not (cid and sec):
            return (False, "this host has no Google OAuth client configured", "")
        try:
            token = t.exchange_code(code, cid, sec, _redirect_uri(self))
            access = str(token.get("access_token") or "")
            if not access:
                return (False, f"Google returned no access token: {json.dumps(token)[:200]}", "")
            who = t.identify(access)
        except Exception as exc:
            return (False, f"the sign-in could not be completed: {exc}", "")
        sub = str(who.get("sub") or "")
        email = str(who.get("email") or "")
        name = str(who.get("name") or "") or (email.split("@")[0] if email else "")
        if not (sub and email):
            return (False, "Google did not return an account identity", "")
        try:
            tenant = t.ensure_tenant(sub, email, name)
        except TenancyError as exc:
            return (False, str(exc), "")
        try:
            t.store_token(tenant, token, email)
        except OSError as exc:
            return (False, f"the sign-in worked but the token could not be stored: {exc}", "")
        cookie_value, expires = t.start_session(tenant.slug)
        import time as _t

        age = max(0, expires - int(_t.time()))
        secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
        cookie = (f"jha_session={cookie_value}; Path=/; Max-Age={age}; HttpOnly; "
                  f"SameSite=Lax{secure}")
        print(f"sign-in: {email} -> tenant {tenant.slug} ({len(t.granted_scopes(tenant))} scope(s) granted)")
        return (True, f"Signed in as {email}. Your hunt is at {tenant.slug}.", cookie)

    # ------------------------------------------------------------------ Google sign-in
    def _auth_callback(self):
        q = self._query()
        state = q.get("state", "")
        code = q.get("code", "")
        err = q.get("error", "")
        page = ("<html><head><meta charset='utf-8'><title>jobhunt-agent</title>"
                "<style>body{background:#0b0d10;color:#e6e9ee;font:15px/1.6 -apple-system,system-ui,sans-serif;"
                "padding:48px;max-width:640px;margin:0 auto}h1{font-family:Georgia,serif;font-weight:600}"
                "p{color:#8b95a3}a{color:#60a5fa;font-size:14px}</style></head><body>")
        if err:
            body = f"<h1>Not connected</h1><p>Google returned: {err}. Nothing changed.</p>"
        elif not code or not _STATE.check(state):
            body = ("<h1>Not connected</h1><p>This response did not match a sign-in that started here, or it "
                    "took too long. Nothing changed - open the app and press Continue with Google again.</p>")
        elif Handler.tenancy is not None and Handler.tenancy.mode == "multi":
            ok, msg, cookie = self._multi_signin(code, state)
            if cookie:
                self.send_response(303)
                self.send_header("Set-Cookie", cookie)
                self.send_header("Location", "/app/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = (f"<h1>{'Connected' if ok else 'Not connected'}</h1><p>{msg}</p>")
        else:
            ok, msg = auth_exchange(code, self.headers.get("Host", ""), state)
            body = (f"<h1>{'Connected' if ok else 'Not connected'}</h1><p>{msg}</p>")
        page += body + "<p><a href='/app/'>Back to the app</a></p></body></html>"
        return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if snapshot_path() is not None and path != "/api/sync":
            # A viewer can show a deployment; it can never drive one. The push snapshot is the only way in.
            return self._json({"ok": False, "error": "this instance is a read-only view of a deployment"},
                              405)
        # In multi-tenant mode a user writes to their own tenant through their session; the operator token
        # stays for operator routes.
        if Handler.tenancy is not None and Handler.tenancy.mode == "multi" and path != "/api/sync":
            if not self._may_write():
                return self._json({"ok": False, "needs_login": True,
                                   "error": "sign in to change your own settings"}, 401)
        if path == "/api/sync":
            # The pushing deployment authenticates with the same operator token. A viewer accepts data and
            # nothing else; it never acts on it.
            if not self.token or not self._authed():
                return self._json({"ok": False, "error": "unauthorised: X-Dashboard-Token required"}, 401)
            target = snapshot_path()
            if target is None:
                return self._json({"ok": False, "error": "JHA_SNAPSHOT is not set on this instance"}, 400)
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0 or length > SNAPSHOT_MAX_BYTES:
                return self._json({"ok": False, "error": f"a snapshot body between 1 and "
                                                        f"{SNAPSHOT_MAX_BYTES} bytes is required"}, 413)
            raw = self.rfile.read(length)
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return self._json({"ok": False, "error": f"the snapshot is not valid JSON: {exc}"}, 400)
            routes = (parsed or {}).get("routes") if isinstance(parsed, dict) else None
            needed = ("/api/state", "/api/usage", "/api/alerts", "/api/config/dials")
            missing = [r for r in needed if not isinstance(routes, dict) or r not in routes]
            if missing:
                # A malformed push must never replace a good snapshot: the published view would go blank and
                # nothing would say why.
                return self._json({"ok": False,
                                   "error": "the snapshot is missing " + ", ".join(missing)
                                            + "; a good snapshot was left in place"}, 400)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".tmp")
            tmp.write_bytes(raw)
            tmp.replace(target)
            print(f"snapshot accepted: {len(raw)} bytes, {len(parsed.get('documents') or {})} pack(s), "
                  f"generated {parsed.get('generated_at')}")
            return self._json({"ok": True, "bytes": len(raw),
                               "documents": len(parsed.get("documents") or {}),
                               "generated_at": parsed.get("generated_at")})
        payload = self._body()
        if payload is None:
            return
        if path == "/api/config/preview":
            # a preview computes and writes nothing, so it needs no token: it is a read
            ok, result = config_change(self.cfg_path, payload, write=False)
            return self._json(result, 200 if ok or result.get("refused") else 400)
        if self._deny():
            return
        if path == "/api/config":
            ok, result = config_change(self.cfg_path, payload, write=True)
            return self._json(result, 200 if ok else 400)
        if path in ("/api/notify/test", "/api/control/alert-test"):
            ok, message, detail = alert_test(self.cfg_path, payload)
            if path == "/api/notify/test":
                return self._json({"ok": ok, "message": message, "results": detail.get("results", {})},
                                  200 if ok else 400)
            return self._json({"ok": ok, "action": "alert-test", "message": message, "detail": detail},
                              200 if ok else 400)
        if path in ("/api/notify/channels", "/api/control/channels"):
            ok, message, detail = switch_channels(self.cfg_path, payload)
            if path == "/api/notify/channels":
                body = {"ok": ok, "message": message}
                return self._json(body, 200 if ok else 400)
            return self._json({"ok": ok, "action": "channels", "message": message, "detail": detail},
                              200 if ok else 400)
        if path == "/api/control/pause":
            ok, message, detail = control_toggle(self.cfg_path, "pause", payload.get("job"))
            return self._json({"ok": ok, "action": "pause", "message": message, "detail": detail},
                              200 if ok else 400)
        if path == "/api/control/resume":
            ok, message, detail = control_toggle(self.cfg_path, "resume", payload.get("job"))
            return self._json({"ok": ok, "action": "resume", "message": message, "detail": detail},
                              200 if ok else 400)
        if path == "/api/control/sweep":
            ok, message, detail = control_sweep(self.cfg_path, payload.get("job"))
            return self._json({"ok": ok, "action": "sweep", "message": message, "detail": detail},
                              200 if ok else 400)
        if path == "/api/control/sheet-sync":
            ok, message, detail = control_sheet_sync(self.cfg_path)
            return self._json({"ok": ok, "action": "sheet-sync", "message": message, "detail": detail},
                              200 if ok else 400)
        m = re.fullmatch(r"/api/jobs/([A-Za-z0-9._-]+)/?(resume|pause)?", path)
        if m:
            action = m.group(2) or payload.get("action", "resume")
            cfg = self._cfg()
            ok, msg = toggle_job(profile_for(cfg), m.group(1), action)
            return self._json({"ok": ok, "message": msg}, 200 if ok else 400)
        return self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        if os.environ.get("DASHBOARD_VERBOSE"):
            sys.stderr.write("dashboard: " + _scrub(fmt % args, self._extras()) + "\n")


def _version() -> str:
    try:
        spec = importlib.util.spec_from_file_location("jha_version", ROOT / "engine" / "version.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return str(getattr(mod, "__version__", "") or "")
    except Exception:
        return ""


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    global HERMES_BIN
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", default=str(ROOT / "config" / "tenant.yaml"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("DASHBOARD_PORT", "8787")))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--hermes-bin", default=os.environ.get("JHA_HERMES_BIN", ""),
                    help="scheduler CLI used by the one-click controls (default: PATH, then ~/.local/bin)")
    ap.add_argument("--multi-tenant", action="store_true",
                    default=os.environ.get("JHA_MULTI_TENANT", "") == "1",
                    help="one host, many users: each signs in with Google and sees only their own hunt")
    ap.add_argument("--signup", default=os.environ.get("JHA_SIGNUP", "open"),
                    choices=("open", "closed"), help="whether a new Google account may create an account here")
    ap.add_argument("--max-tenants", type=int, default=int(os.environ.get("JHA_MAX_TENANTS", "0") or 0),
                    help="cap on accounts this host will create (0 = no cap)")
    a = ap.parse_args()
    HERMES_BIN = a.hermes_bin
    Handler.default_cfg_path = pathlib.Path(a.tenant).expanduser()
    Handler.token = os.environ.get("DASHBOARD_TOKEN", "")
    if a.multi_tenant:
        stub = _auth_stub()
        # the stub is refused on a public bind: a test seam must never be an auth bypass
        if stub and os.environ.get("JHA_AUTH_STUB") and str(a.host) not in ("127.0.0.1", "localhost", "::1", ""):
            print("refusing JHA_AUTH_STUB on a non-loopback bind", file=sys.stderr)
            return 3
        Handler.tenancy = Tenancy(
            ROOT, mode="multi", default_cfg=Handler.default_cfg_path,
            signup=a.signup, max_tenants=a.max_tenants,
            config_dir=pathlib.Path(os.environ.get("JHA_CONFIG_DIR", ROOT / "config")).expanduser(),
            hunts_dir=pathlib.Path(os.environ.get("JHA_HUNTS_DIR",
                                                  pathlib.Path.home() / "hunts")).expanduser(),
            profiles_dir=pathlib.Path(os.environ.get("JHA_PROFILES_DIR",
                                                     pathlib.Path.home() / ".hermes" / "profiles")).expanduser(),
            exchange=_stubbed_exchange(stub) if stub else None,
            userinfo=_stubbed_userinfo(stub) if stub else None)
        print(f"multi-tenant: signup={a.signup}, accounts={len(Handler.tenancy.slugs())}, "
              f"configs in {Handler.tenancy.config_dir}, workspaces in {Handler.tenancy.hunts_dir}")
        if a.signup == "closed" and not Handler.tenancy.slugs():
            print("signup is closed and no account exists yet: nobody can sign in", file=sys.stderr)
    loopback = str(a.host) in ("127.0.0.1", "localhost", "::1", "")
    Handler.public = not loopback
    if Handler.public and not Handler.token:
        print(f"refusing to bind {a.host}: a non-loopback bind exposes the tracker, so DASHBOARD_TOKEN "
              f"must be set (every endpoint would need it)", file=sys.stderr)
        return 3
    if not Handler.default_cfg_path.exists():
        print(f"warning: {Handler.default_cfg_path} not found - /api/state will be empty", file=sys.stderr)
    print(f"dashboard on http://{a.host}:{a.port}  tenant={Handler.default_cfg_path}  "
          f"auth={'token' if Handler.token else 'local-only'}  "
          f"hermes={hermes_bin() or 'not found (controls that queue work will say so)'}")
    with Server((a.host, a.port), Handler) as httpd:
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
