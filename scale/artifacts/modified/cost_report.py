#!/usr/bin/env python3
"""cost_report.py - per-tenant cost, plan fit and margin from the engine's usage log.

The engine appends one JSON line per agent run to `usage/<tenant>.jsonl`
(`hermes cron usage_audit.jsonl` merged across profiles, fields: ts, job, prompt_tokens,
completion_tokens, model, error). This turns those lines into money at the provider's two-tier
input rates and compares them with the tenant's plan price.

  python3 tools/cost_report.py                       # all tenants, current month
  python3 tools/cost_report.py --tenant jane-doe --days 30
  python3 tools/cost_report.py --json                # machine-readable (for the dashboard)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.price_model import RATES, run_cost  # noqa: E402

USAGE = ROOT / "usage"
PRICING = ROOT / "pricing.yaml"


def _has_lines(path: pathlib.Path) -> bool:
    try:
        return bool(path.read_text(errors="replace", encoding="utf-8").strip())
    except OSError:
        return False


def load_lines(path: pathlib.Path):
    for line in path.read_text(errors="replace", encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def usage_files() -> dict:
    """Every usage file by tenant, the tenant's OWN ledger first.

    `gates/model_budget.py` appends each run's measured usage to `<workspace>/data/usage.jsonl`, and that is
    the file the account's budget is enforced against; `usage/<slug>.jsonl` is the older per-host meter a
    managed deployment writes. The ledger wins when it has data, so the operator's figure is the one the
    account was actually held to rather than a second total that can disagree with it.
    """
    found: dict = {}
    for cfg_path in sorted((ROOT / "config").glob("tenant*.yaml")):
        if cfg_path.stem in {"tenant.example"}:
            continue
        text = cfg_path.read_text(errors="replace", encoding="utf-8")
        slug = text.split("slug:", 1)[-1].split("\n", 1)[0].strip() if "slug:" in text else cfg_path.stem
        raw = text.split("workspace:", 1)[-1].split("\n", 1)[0].strip().strip('"\'') if "workspace:" in text else ""
        ws = pathlib.Path(raw.format(slug=slug)).expanduser() if raw else pathlib.Path.home() / "hunts" / slug
        found.setdefault(slug, []).append(ws / "data" / "usage.jsonl")
    for f in sorted(USAGE.glob("*.jsonl")):
        found.setdefault(f.stem, []).append(f)
    return found


def tenant_costs(days: int):
    out = {}
    for tenant, candidates in usage_files().items():
        files = [f for f in candidates if f.is_file()]
        if not files:
            continue
        # the tenant's own ledger is the source the budget gate uses; the meter is the fallback
        f = files[0] if _has_lines(files[0]) else files[-1]
        if f in files[1:] and not _has_lines(f):
            continue
        totals = {"runs": 0, "sweeps": 0, "mail": 0, "prompt_tokens": 0,
                  "completion_tokens": 0, "cost": 0.0, "errors": 0}
        for d in load_lines(f):
            runs_in_line = 1
            try:
                runs_in_line = max(1, int(d.get("runs") or 1))
            except (TypeError, ValueError):
                runs_in_line = 1
            ts = str(d.get("ts", ""))
            if days and ts:
                import datetime
                try:
                    when = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    age = (datetime.datetime.now(datetime.timezone.utc) - when).days
                    if age > days:
                        continue
                except Exception:
                    pass
            pt = int(d.get("prompt_tokens", 0))
            ct = int(d.get("completion_tokens", 0))
            totals["runs"] += runs_in_line
            totals["prompt_tokens"] += pt
            totals["completion_tokens"] += ct
            totals["cost"] += run_cost(pt, ct)
            if pt > 2_000_000:
                totals["sweeps"] += 1
            elif pt > 100_000:
                totals["mail"] += 1
            if d.get("error"):
                totals["errors"] += 1
        out[tenant] = totals
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    pricing = json.loads(PRICING.read_text(encoding="utf-8")) if PRICING.exists() else {"plans": []}
    plan_price = {p["id"]: p["price_usd_month"] for p in pricing.get("plans", [])}
    plan_runs = {p["id"]: p["limits"].get("agent_runs_included_month") for p in pricing.get("plans", [])}
    plan_of = {}
    for cfg in (ROOT / "config").glob("tenant*.yaml"):
        txt = cfg.read_text(errors="replace", encoding="utf-8")
        slug = txt.split("slug:", 1)[-1].split("\n", 1)[0].strip() if "slug:" in txt else cfg.stem
        plan = txt.split("plan:", 1)[-1].split("\n", 1)[0].strip() if "plan:" in txt else "starter"
        plan_of[slug] = plan

    costs = tenant_costs(a.days)
    if a.tenant:
        costs = {k: v for k, v in costs.items() if k == a.tenant}
    if a.json:
        print(json.dumps(costs, indent=2))
        return 0
    if not costs:
        print(f"no usage recorded for any tenant (looked at each workspace's data/usage.jsonl and {USAGE})")
        return 0

    print(f"window: last {a.days} days | provider {RATES}")
    print("source: each account's own ledger (<workspace>/data/usage.jsonl) where it has data, "
          f"else the per-host meter ({USAGE.name}/)")
    print(f"{'tenant':16} {'plan':9} {'runs':>5} {'sweeps':>7} {'mail':>5} "
          f"{'cost$':>8} {'price$':>7} {'margin':>7} {'over cap':>9}")
    total_cost = total_price = 0.0
    for tenant, t in sorted(costs.items()):
        plan = plan_of.get(tenant, "starter")
        price = plan_price.get(plan, 0)
        cap = plan_runs.get(plan)
        over = max(0, t["runs"] - cap) if cap else 0
        margin = (price / t["cost"]) if t["cost"] else float("inf")
        total_cost += t["cost"]
        total_price += price
        print(f"{tenant[:16]:16} {plan:9} {t['runs']:5d} {t['sweeps']:7d} {t['mail']:5d} "
              f"{t['cost']:8.2f} {price:7.2f} {margin:6.2f}x {over:9d}")
    print(f"{'TOTAL':16} {'':9} {'':5} {'':7} {'':5} {total_cost:8.2f} {total_price:7.2f} "
          f"{(total_price / total_cost if total_cost else 0):6.2f}x")
    print("\nmargin floor is 2.0x (pricing.yaml); anything below it means the plan's schedule or the "
          "cache-hit ratio has drifted - re-run tools/price_model.py and adjust the plan cadence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
