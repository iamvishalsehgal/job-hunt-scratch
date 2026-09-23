# Where a sweep's tokens actually go — measured

Every number here is read off this host, not estimated. Sources:

* `~/.hermes/profiles/<slug>/logs/agent.log` — one line per API call, with the real token counts:
  `API call #N: model=deepseek-flash provider=deepseek in=64044 out=1021 total=65065 cache=61696/64044 (96%)`
* `~/.hermes/profiles/<slug>/cron/executions.db` — how often the sweep job actually fired.
* `~/.hermes/profiles/<slug>/cron/output/<job-id>/<ts>.md` — the run artefacts.
* `~/.hermes/profiles/<slug>/cron/jobs.json` plus its `.bak-*` files — the prompt-size history.

The scripts that produced it are `analyze_tokens.py`, `analyze_prompt_series.py` and `regress.py` in
this directory.

## 1. The prompt's token size, measured instead of assumed

The usual `chars / 4` is close but it is a guess. Two sessions per candidate, chosen because their
prompt sizes are far apart and nothing else material changed between them:

| candidate | session A | session B | Δchars | Δinput tokens | chars/token |
|---|---|---|---|---|---|
| vishal | 2026-09-21 23:36 — 36,725 chars, first call in=25,776 | 2026-09-22 22:00 — 67,878 chars, in=33,192 | +31,153 | +7,416 | **4.20** |
| nhung  | 2026-09-21 21:28 — 50,790 chars, first call in=24,614 | 2026-09-22 22:00 — 63,440 chars, in=27,893 | +12,650 | +3,279 | **3.86** |

Mean **4.03 chars/token**. A least-squares fit over all 18 logged sweep sessions is far weaker
(slope 0.094 tokens/char, R² 0.16) because the base context moves independently; the anchor pairs above
are the defensible estimate and they bracket `chars/4` from both sides.

So, before the change:

| candidate | prompt chars | prompt tokens/call |
|---|---|---|
| vishal | 69,772 | 17,313 |
| nhung | 65,334 | 16,212 |

That is the ~17k/call the brief quotes, and 17,313 × 54 calls ≈ **0.93M prompt input tokens per sweep**
— the ~1M the brief quotes, confirmed.

## 2. What one sweep costs, end to end

Grouped by session id, over every logged sweep session (vishal job `7cc9661411f2`, nhung job `f5d11d205715`):

| candidate | sessions | calls/sweep (median) | input tokens/sweep (median) | cache hit | uncached input/sweep | output tokens/sweep | prompt share of input |
|---|---|---|---|---|---|---|---|
| vishal | 10 | 54 | 4,538,564 | 98.2% | 86,608 | 34,236 | 22.1% |
| nhung | 22 | 96 | 7,460,328 | 97.6% | 178,003 | 58,360 | 21.7% |
| both | 32 | 70 | 5,903,508 | 97.8% | 134,674 | 54,479 | 21.7% |

Observations that matter more than the prompt size:

* **The prompt is ~22% of input tokens, and it is the only part that is fully static.** Everything else
  is conversation growth, which is driven by how many turns the sweep takes.
* **Cache hits are 97.6–98.2%.** The prompt is the cached prefix, so the tokens it costs are mostly
  cache-priced. The cash saving from shrinking it is much smaller than the token saving; the honest
  lever is the uncached share (86k–178k/sweep), which is where tool output and growth land.
* **Calls per sweep, not characters, is the cost multiplier.** nhung pays 96 calls where vishal pays 54,
  and her prompt is *smaller*.

## 3. The sweep does not run every 10 minutes

`jobs.json` says `interval: 10m`, and the brief reads that as 144 rounds/day. `executions.db` says
otherwise — measured firings of the sweep job:

| candidate | runs | 2026-09-19 | 09-20 | 09-21 | 09-22 |
|---|---|---|---|---|---|
| vishal (`7cc9661411f2`) | 10 | – | – | 1 | **9** |
| nhung (`f5d11d205715`) | 25 | 2 | 7 | 7 | **9** |

The 10-minute interval is the *tick*; the sweep itself is guarded down to roughly every 2.6h by its own
"BATCH HARD — 3-HOURLY RUN" rule. So the real cadence is **9 sweeps/day per candidate, 18/day across
both** — not 288. Any cost figure built on 144/day overstates by 16×. (The vishal-mail job does run on
the 10-minute tick: 72 executions on 09-22.)

## 4. Daily prompt cost, before and after

At the measured 4.03 chars/token, the measured calls/sweep, and the measured 9 sweeps/day:

| candidate | before (tokens/call → /day) | after | saved/day |
|---|---|---|---|
| vishal | 17,313 × 54 × 9 = 8,414,192 | 15,180 × 54 × 9 = 7,377,432 | **1,036,760** |
| nhung | 16,212 × 96 × 9 = 14,007,091 | 14,202 × 96 × 9 = 12,270,301 | **1,736,790** |
| **both** | 22.4M | 19.6M | **2.77M tokens/day** |

That is ~115k tokens/sweep (vishal) and ~193k (nhung) off the re-send, ~2.77M/day, ~83M/month across
the two candidates.

## 5. What that saves in money, honestly

Not the full 2.77M: the prompt sits in the cached prefix, so most of the removed tokens were
cache-priced already. The saving that is definitely real is

* the **uncached share of the prompt** — 2–3% of the prompt tokens are billed at full rate every call;
* the **cache-miss turns**: when the prefix changes mid-sweep, the whole prompt is re-billed uncached;
* the **output** side is untouched by this change (median 34k/58k output tokens/sweep);
* and a playbook **re-enters the context when it is read**, from that turn onward. So a 1,900-char block
  read at turn 20 of 54 costs 20/54 of what it used to cost, and a block whose step is never reached
  costs nothing at all. The prompt's own measured warning — two sub-agent answers at 93,172 and 65,425
  characters, each re-paid on every later turn — is the same mechanism working against us.

So treat the headline as **"~2.8M prompt tokens/day stop being re-sent"**, with the cash effect
concentrated in the uncached slice and in the turn count. The number that would move money fastest is
`calls/sweep` (nhung 96), not `prompt chars`.

## 6. The prompt also dominates the run artefacts

The nine sweep outputs in `cron/output/7cc9661411f2/` total 442,310 chars; the prompt echo inside them
is 99.4% of that and the actual response is **0.6%** (median 448 chars, and 4 of 9 runs answered exactly
`[SILENT]`, 22 chars). The prompt is therefore paid for three times over: every API call, every
sub-agent turn that inherits it, and every artefact written to disk.

## 7. Prompt drift between the two live tenants (found while measuring)

* nhung's prompt carries `## VERIFICATION CODES, FORM RECIPES AND THE CV PIPELINE` **four times**
  (2,095 chars of it, ~520 tokens/call); vishal carries it once. Pure duplication.
* nhung has **no `## LESSONS` section at all**; vishal has one (2,228 chars). A rule vishal gets, nhung
  silently does not.
* The two live prompts (vishal 37 sections, nhung 39) have drifted well past the repo template (26
  sections). Sections the live sweeps rely on but the template never had: `OUTBOUND MAIL TO AN
  EMPLOYER`, `HARD GATES`, `ROUTE SELECTION`, `ACCOUNT HANDLING AND VERIFICATION`, `DEFERRALS AND
  INTERVIEW DEADLINES`, `WHEN A GATE REFUSES`, `EVERY APPLICATION CARRIES A CV`, `BATCH HARD`, `FIT
  PRIORITY`, `UNLIMITED PLAN`, `REJECTION MEMORY`. A fresh tenant provisioned from the template today
  gets a materially weaker sweep than the live two.

## 8. Next tier (not moved by this change)

Measured on the vishal prompt. These are static blocks consulted at a step, so the same treatment
applies — but each should be a deliberate decision, not a sweep:

| section | chars (vishal) | when it is actually needed |
|---|---|---|
| ACCOUNT HANDLING AND VERIFICATION | 3,190 | only when creating a portal account |
| ROUTE SELECTION | 2,857 | once, when choosing the route per posting |
| DEFERRALS AND INTERVIEW DEADLINES | 1,987 | only when a deadline/interview exists |
| WHEN A GATE REFUSES, FIX THE DRAFT AND SEND AGAIN | 1,714 | only after a gate refusal |
| INTERVIEW PACK | 1,694 | only when an interview date+time is confirmed |
| REJECTION MEMORY | 1,385 | only on a rejection |
| **total** | **12,827 chars ≈ 3,183 tokens/call** | another −18% on vishal |

Do **not** move: `HARD GATES` and `WHEN THE AUTOMATIC APPLY FAILS` (read off the live prompt by
`engine/tools/prompt_drift_check.py`), `WORKLOAD THROTTLE` (read by
`tests/test_prompt_drift_backoff.py`), and `BATCH HARD` / `UNLIMITED PLAN` / `SUB-AGENT DISCIPLINE` /
`REPORTING`, which every sweep reaches.

## 9. Reproduce

```bash
cd /home/ubuntu/jobhunt-agent
python3 ~/job-hunt-scratch/scale/analyze_tokens.py          # per-session token totals
python3 ~/job-hunt-scratch/scale/analyze_prompt_series.py   # prompt-size history vs measured input
python3 engine/tools/prompt_budget.py                       # current chars, tokens/call, markers
python3 engine/tools/prompt_budget.py --template
```

## 10. Note: the live prompts moved on after the move

The sizes in §4 are the sizes at the moment of the move. The stores keep being edited — a concurrent
change appended a `MODEL BUDGET` bullet to the `WORKLOAD THROTTLE` section of both live prompts a few
minutes later — so `prompt_budget.py` now prints a slightly smaller saving on the live stores than the
move itself achieved:

| candidate | before the move | immediately after | now (live store) | move only | tool now shows |
|---|---|---|---|---|---|
| vishal | 69,772 | 61,175 | 62,917 | −8,597 (−12.3%) | −6,855 (−9.8%) |
| nhung | 65,334 | 57,233 | 58,969 | −8,101 (−12.4%) | −6,365 (−9.7%) |

That bullet lives inside `WORKLOAD THROTTLE`, which the registry deliberately refuses to move (see
`KEEP_IN_PROMPT` in `engine/tools/prompt_playbook.py`: `tests/test_prompt_drift_backoff.py` reads that
section off the live prompt). So a later edit to it is unaffected by this change, and the −12.3%/−12.4%
figures remain the honest measure of what the move saved.

`prompt_budget.py` multiplies by a pooled median of 58 calls/sweep so it can score any store; §4 uses the
per-candidate medians (54 and 96), which is why the two tables differ slightly.
