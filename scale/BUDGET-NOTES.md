# Per-account model budget (jobhunt-agent) - what landed, and how to prove it

Blocker closed: "no per-account model budget". One tenant's sweeps could spend without limit, and no surface
said what an account had cost. Measured on 22 Sep 2026 before this work: vishal $2.67/24h and nhung
$2.75/24h against a $39/month plan (the plans' own cost basis is ~$0.40/day each).

## The three pieces

1. LEDGER - `engine/gates/model_budget.py record` appends one line per run to
   `<workspace>/data/usage.jsonl`: ts, slug, run_id, job, kind (sweep|mail|run), model, prompt_tokens,
   completion_tokens, total_tokens, runs, cost_usd, source, recorded_by. The numbers are measured from the
   engine's own audit (`<profile>/cron/usage_audit.jsonl`), never self-reported by the agent, and priced with
   the product's one two-tier model (tools/price_model.py). Idempotent by run_id, so a retry cannot
   double-count. This is the tenant's own state, beside its other per-run ledgers.
2. DIAL - `budget: {daily_usd, on_exceed: warn|throttle|stop, throttle_rate}` in the tenant config, and
   `engine/gates/model_budget.py ask --plan-cap N` prints the volume this run may use: exit 0 = full cap,
   72 = throttled (a decision, not an error), 70 = do not run (the subscriber set `stop`). A missing,
   truncated or nonsensical dial degrades to the built-in default (warn at $1.00/day), says so, and NEVER
   changes the run's volume - a broken file must not slow a paid hunt.
3. SURFACES - the dashboard carries the state in `/api/usage` and `/api/alerts` (beside the interview
   backoff), and Settings can change the dial (`budget` is in `dials_state()["writable"]`); the same two
   fields are read by `dials_state`, `cfg_view` and the write path in `_render_edits`. The operator's CLI
   (`tools/cost_report.py`) reads each account's own ledger.

## Files

new: engine/gates/model_budget.py, tests/test_model_budget.py
modified: dashboard/server.py, dashboard/app/app.js, provisioning/provision_tenant.py,
engine/scripts/tenant_config.py, engine/cron/jobs.template.json, engine/tools/prompt_budget.py,
config/tenant.example.yaml, config/tenant.yaml (live dial), tools/cost_report.py, tests/test_dashboard.py

## Proof

    cd /home/ubuntu/jobhunt-agent
    python3 -m unittest $(ls tests/test_*.py | sed 's|/|.|g; s|\.py$||')      # 809 ran, 3 environmental
    python3 -m unittest tests.test_model_budget                               # 51 ok
    python3 tools/cost_report.py                                             # operator view
    cd ~/.hermes/profiles/vishal/workspace && python3 gates/model_budget.py ask --plan-cap 30
    curl -s http://127.0.0.1:8787/api/usage | python3 -m json.tool | grep -A4 budget

The 3 failures are `pipeline_watchdog.sh` reporting "SWAP IN USE" (the VM is under memory pressure right
now): they fail identically in a pristine `git worktree` of HEAD, i.e. independently of any of these edits.
Proven with `git worktree add /tmp/jha-pristine HEAD`.

## Live state after deploying

    nhung:  gate installed, dial -> config.json, today $2.75 (39 runs)
    vishal: gate installed, dial -> config.json, today $2.67 (35 runs)
    /api/usage: runs 35, spend $2.6677, source "this account's own ledger",
                dial $3.00/day warn, remaining $0.33, sentence "one more sweep would cross it"

Both live sweep prompts now ask the gate before spending and record the run at the end; the Settings dial
is live behind the restarted dashboard (jobhunt-dashboard.service).

## Hazard to know about

A CONCURRENT agent session is editing this checkout. provisioning/provision_tenant.py and
engine/cron/jobs.template.json were rewritten at 22:40:15 with versions predating this work, silently
reverting two edits. They were re-applied idempotently (`~/job-hunt-scratch/scale/reapply_repo_edits.py`)
and verified to survive the full test run; re-check `grep -c model_budget provisioning/provision_tenant.py`
before trusting the tree.
