# Scale audit — how many candidate tenants fit on this one Oracle Always Free box

Measured on the live host over ssh, 2026-09-22 22:04–22:20 UTC. Read-only: no repo,
cron, or workspace was changed. Every number below is lifted from the running host;
every claim carries a path:line.

Host: `134.98.157.102` — Oracle A1.Flex Always Free, aarch64 Neoverse-N1, **4 OCPU /
23,974 MB RAM / 96 GB disk**, uptime 3 d 3 h 37 m.

---

## 0. What is actually running (the baseline for every ceiling)

| Thing | Count | Evidence |
|---|---|---|
| Hermes gateways | 3 (`default`, `vishal`, `nhung`) | `systemctl --user list-units` → `hermes-gateway{,-vishal,-nhung}.service`; pids 26017 / 324400 / 26019 |
| cron jobs defined | 14 (default 6, vishal 5, nhung 3) | `~/.hermes/cron/jobs.json`, `~/.hermes/profiles/{vishal,nhung}/cron/jobs.json` |
| Headless chromium | 3 (one per tenant) | `bu-chrome{,-vishal,-nhung}.service`, CDP 9222/9223/9224 |
| chrome processes | 269 total, 262 chrome-named | process tree walk at 22:05 |
| Tenant-scaffolded but empty | 1 (`jane-doe`) | `~/.hermes/profiles/jane-doe/` is empty — no workspace, no `jobs.json`, no gateway |
| Deliberate ballast | 6 GB RAM + 1 niced core | `jobhunt-keepalive.service` (`KEEPALIVE_GB=6`, `OOMScoreAdjust=1000`), `jobhunt-keepalive-cpu.service` (`nice 19` spinner) |

**Marginal cost of one new tenant** (derived from the empty `jane-doe` scaffold, not
guessed): 1 gateway process (~205 MB PSS measured) + 1 chromium + 1 profile dir.
That is the unit every ceiling below is divided by.

---

## 1. What breaks first, in order — with the measured ceiling

### 1st: CPU + browser-process health — already at the line at 3 tenants

- `uptime`: load average **4.39 / 2.49 / 1.94** and climbing during the audit
  (**5.67 / 4.66 / 3.09** twelve minutes later) on **4** cores. Load ≥ cores with the
  job-hunts at ~10 % duty cycle (below).
- 10-second CPU accounting by process group (`/proc/<pid>/stat` deltas):
  **2.48 of 4 cores busy (62 %)** — chrome **1.01 cores**, `cron.scheduler` 0.42,
  keepalive spinner ~1 core (niced), gateways 0.01.
- chrome is the CPU owner, and it is also the most fragile part:
  **445–469 `CDP supervisor … crashed` lines** in
  `~/.hermes/profiles/nhung/logs/errors.log` (1,828-line file). Worst offenders:
  `sa-1-d7989021` ×98, `cron:1d7670ad2d44:…` ×42, `sa-0-26beb1db` ×37,
  `cron:f5d11d205715:…` ×24. Peak hours 01:00 ×146, 18:00 ×63, 04:00 ×55.
  Crash site: `hermes-agent/tools/browser_supervisor.py:326`.
- Tabs are never reaped. Live CDP target counts:
  **default 30 tabs / 64 targets, nhung 217 tabs / 494 targets, vishal 16 tabs / 24
  targets** (`http://127.0.0.1:{9222,9223,9224}/json/list`).
- Dispatch is already late: `last_dispatch.lateness_seconds` **51.1** (vishal) and
  **54.6** (nhung) in their `jobs.json`.

**Ceiling: ~4 tenants** before sweep latency inflation becomes the normal state, because
a single tenant's sweep burst (10 sub-agents driving that tenant's one browser) already
pushes the box past 4 cores when two sweeps coincide.

### 2nd: RAM — 3.7–4.2 GB of real headroom, and one leaky browser eats it

- `free -m`: total 23,974 / used 19,792–20,288 / **available 3,686–4,181 MB**
  / shared 6,148 MB. Swap 8,191 MB, 1 MB used.
- System total **PSS 19.17 GB**. By owner (PSS from `/proc/<pid>/smaps_rollup` —
  accurate, individual RSS double-counts shared pages: summed RSS reads 40.44 GB):

  | Owner | PSS | Procs |
  |---|---|---|
  | chrome, all tenants | **10.73 GB** | 269 |
  | `mem-ballast.py` (deliberate) | **6.15 GB** | 1 |
  | 3 gateways | 0.61 GB | 3 |
  | 2 `cron.scheduler` workers | 0.41 GB | 2 |

- Per-tenant browser: **default 1,685 MB / 52 procs / 30 tabs**,
  **vishal 1,088 MB / 36 procs / 16 tabs**, **nhung 8,215 MB / 174 procs / 217 tabs**.
  So a healthy tenant browser is ~1.1–1.7 GB, and a leaky one is **8.2 GB (5×)**.
- No OOM kill anywhere (`dmesg -T`, `journalctl --since "3 days ago"`: zero hits).
  `mem-ballast` carries `OOMScoreAdjust=1000`, so it is the first to die — meaning RAM
  pressure currently surfaces as **browser crashes and 12→49 min sweeps**, not as an
  OOM event. That is why the crash count, not a kernel log, is the RAM signal.

**Ceiling: 5 tenants nominal** ((24 − 6 ballast − 10.7 chrome − 1.0 gateways) ÷ ~1.5 GB
≈ 4 more, ~5 total) — but **≤3 if any tenant's browser leaks tabs**, which is the
observed case.

### 3rd: the scheduler's own fan-out — unbounded today

- Per sweep the prompt allows **"at most 8 pack agents per sweep (8 × batch-size 4 = 32
  roles) plus at most 2 discovery agents"**: `vishal-job-hunt` prompt line 644,
  `nhung-job-hunt` prompt line 567.
- Sub-agents are real and observed: ids come from
  `hermes-agent/tools/delegate_tool.py:195` (`sa-{task_index}-{uuid}`); indices seen in
  logs `{0:232, 1:330, 2:121, 3:28}` → 4-deep concurrent sub-agent work.
- **`cron.max_parallel_jobs` is unset in all three `config.yaml`** (`~/.hermes/config.yaml:110`
  `cron:` holds only `model: deepseek-flash`; same at `profiles/*/config.yaml:110`).
  `_resolve_max_parallel_workers()` (`cron/scheduler.py:3783-3797`) therefore returns
  **`None` → unbounded**, and `_get_parallel_pool` (`cron/scheduler.py:991-1000`) hands
  that to `ThreadPoolExecutor`, i.e. the stdlib default `min(32, cpu+4)` = **8 concurrent
  cron jobs per gateway**. Three gateways ⇒ **up to 24 concurrent cron jobs × up to 10
  sub-agents each**, with nothing global bounding the total.

**Ceiling: this is the amplifier.** Adding tenants multiplies sub-agents linearly
(2 tenants ≈ 20 sub-agents per sweep wave) while no config caps it.

### 4th: the shared LinkedIn guest API (discovery) — the first *external* wall

- Endpoint `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`,
  called at `profiles/*/workspace/discovery/_sweep_c.py:44-45`.
- Requests **per sweep**: NL 20 keywords × 4 offsets (0/25/50/75) = **80**, plus DE 4 +
  IE 4 + FR 4 = **92 total** (`_sweep_c.py:18-38`).
- Serialized: `time.sleep(1.0)` between requests, up to 4 attempts with
  `time.sleep(4 * (attempt + 1))` backoff (`_sweep_c.py:47-55`, `:121`) ⇒ **≥92 s floor
  per sweep, before retries**.
- **No response cache.** The request list is rebuilt every run and `results.json` is a
  per-run append ("Resumable: results.json is appended after every request",
  `_sweep_c.py:3-5`) — the *same* 92 queries are re-issued on every fire.
- One egress IP for all tenants (single VM, single OS user `ubuntu`).
- Currently **not** rate-limited: recorded HTTP codes in discovery artifacts are
  `200 ×359`, no 429/4xx/5xx entries, and grep for real 429s in all 18 logs returned only
  millisecond-timestamp false positives (e.g. `07:34:34,429`).

**Ceiling: ~3–4 tenants** (~300 guest-API requests per 10-min window from one IP) unless
discovery is cached and/or egress moves off-VM.

### 5th: Google Sheets write quota — distant, but structurally shared

- The Sheet is the tracker; a row write pushes inline (`workspace/tools/jt.py:760`,
  `verify_and_push`, called at `jt.py:432/481/717`), and
  `profiles/*/scripts/sync_tracker_to_sheets.sh` is the 360-min catch-up net.
- Both tenants go through **one shared script**, `~/.hermes/scripts/push_trackers_to_sheets.py`,
  parameterized by `--who`: it clears the range then rewrites it
  (`values().clear` line 303 → `values().update` line 304; `batchUpdate` line 183).
- **Zero quota errors in any log** (`quota`/`RESOURCE_EXHAUSTED` → 0 hits across all 18 logs).

**Ceiling: ~10–20 tenants.** Sheets quota is per GCP *project*, so every tenant whose
OAuth lives in the same project shares the ~300 writes/min — that is why this one must
move off-VM before it bites, not after.

### Not a near-term limit

- **Disk**: 24 GB of 96 GB used (**25 %**), inodes **5 %**. Scratch churn measured at
  194 workspace files + 730 `/tmp` entries in the last hour; `/tmp` holds 29,073 entries
  / 2.0 GB but only 215 older than a day. `~/.hermes` 2.8 GB, `~/.cache` 2.0 GB,
  per-profile workspaces 34–42 MB. **~15–20 tenants** before this matters.
- **Telegram**: per-tenant bot tokens (distinct — vishal `4c7029c8ed40`,
  nhung `fe8d54c943b3`), so send limits are per-bot and notify-volume only. Zero flood/429
  evidence. **Not a scaling factor.**
- **LLM provider**: off-VM by definition, and **already failing** — see §4.

### The honest "breaks first" answer

1. **CPU + browser health** (load 4.39→5.67 on 4 cores, 445 CDP crashes, 217-tab browser).
2. **RAM headroom** (3.7–4.2 GB; one leaky browser = 8.2 GB).
3. **Scheduler fan-out / sweep latency** (unbounded workers; sweep longer than its own interval).
4. **LinkedIn guest API** — first genuinely external wall.
5. **Sheets quota** (shared GCP project) → **LLM credit** (already returning 402) → disk → Telegram.

---

## 2. Is per-tenant isolation real?

**Yes for the things that matter, with caveats.** Verified genuinely separate:

| Resource | Proof |
|---|---|
| Profile root, workspace | `~/.hermes/profiles/{vishal,nhung}/workspace` exist; `jane-doe` empty |
| Job store, execution ledger | `profiles/<slug>/cron/jobs.json` (91 KB / 83 KB) and `executions.db` (115 KB / 188 KB) per profile |
| Session state | `profiles/nhung/state.db` 134 MB, `profiles/vishal/state.db` 36 MB, `~/.hermes/state.db` 52 MB |
| Browser profile + CDP port | `bu-chrome.service` → `--user-data-dir=/home/ubuntu/.bu-profile` :9222; `bu-chrome-nhung.service` → `.bu-profile-nhung` :9223; `bu-chrome-vishal.service` → `.bu-profile-vishal` :9224 |
| Telegram identity | distinct `.telegram-token` per profile (md5 differ) |
| Google identity | distinct `google_token.json` per profile (md5 differ) |
| Tracker target | per-profile `tracker_sheets.json` → vishal `1JyHCZ…`, nhung `1C4-ML…` |
| Mail ledger | `profiles/*/workspace/data/apply-email-ledger.json` |

**Shared mutable state found (each with its path):**

1. **`/tmp` — one namespace for all tenants.** 29,073 entries, 2.0 GB, no reaper.
   Tenant-identifying artefacts sit in fixed-ish names: `/tmp/tracker_export_vishal.json`,
   `/tmp/jha-apply-email-*` (×4 at once), `/tmp/recip-*` (×3), `/tmp/wants-*`, `/tmp/draft-*`,
   `/tmp/nobbrief-*`. Any two tenants that ever pick the same name collide, and nothing
   cleans up.
2. **`~/job-hunt-scratch/` — cross-tenant scratch**, referenced by *both* job-hunt prompts
   (vishal's prompt refs `~/job-hunt-scratch/`, nhung's too). 31 MB, 27 entries.
3. **`/home/ubuntu/.hermes/scripts/push_trackers_to_sheets.py`** — the single Sheets writer
   for every tenant (`--who` selects the target). A bad edit or a bug in the `--who`
   resolution writes the wrong candidate's sheet; isolation is a flag, not a boundary.
4. **`/home/ubuntu/.hermes/tracker_sheets.json`** — one top-level map holding both tenants'
   spreadsheet ids (a second copy exists per profile, which is what the sync script reads,
   so this one is belt-and-braces but still shared).
5. **`/home/ubuntu/.hermes/mail_seen.txt`** (651 B) — a single global "seen mail" file;
   vishal's prompt references it as `~/.hermes/scripts/../mail_seen.txt`.
6. **`/home/ubuntu/.cache/ms-playwright/chromium-1234`** — one browser binary shared by all
   three chromium instances (read-mostly, low risk, but a version bump hits everyone).
7. **One OS user (`ubuntu`), one egress IP, one disk/inode budget, one /dev/shm (12 GB
   tmpfs, currently empty).** So the shared *outbound* reputation surface — LinkedIn guest
   API rate limit and outbound mail IP — is global by construction.
8. **No cross-tenant scheduling coordination.** The in-flight guard is per-process:
   `try_register_running_job` / `_running_job_ids` (`cron/scheduler.py:605-625`). A tenant
   mid-sweep cannot yield to another tenant's sweep; the three gateways each do their own
   thing against the same 4 cores.
9. **Global ballast**: `mem-ballast` (6 GB) + the CPU spinner count against every tenant
   (`jobhunt-keepalive*.service`).

---

## 3. Changes that make this hold N tenants, in priority order

**In-VM, cheapest-leverage first:**

1. **Cap the fan-out.** Set `cron.max_parallel_jobs` in `/home/ubuntu/.hermes/config.yaml:110`
   and `/home/ubuntu/.hermes/profiles/*/config.yaml:110` (or export `HERMES_CRON_MAX_PARALLEL`,
   read at `cron/scheduler.py:3783-3790`). Today it is unset ⇒ 8 jobs/gateway × 3 gateways,
   each spawning up to 10 sub-agents. This is the single highest-leverage line in the system.
2. **Reap tabs and cap browser memory.** Add a tab-count/PSS watchdog that restarts the
   tenant's chromium past a threshold (nhung is at 217 tabs / 8.2 GB). Touches the crash
   site `tools/browser_supervisor.py:326` and the units
   `~/.config/systemd/user/bu-chrome{,-vishal,-nhung}.service`.
3. **Make the sweep cadence honest.** `job-hunt` interval is 10 min in
   `profiles/*/cron/jobs.json`, but measured duration is **12.2 min avg / 23.4 max** (vishal)
   and **18.9 avg / 49.5 max** (nhung). Duration > interval by design, so fires landing
   mid-run are silently dropped by the in-flight guard (`cron/scheduler.py:605-625`), and
   the stale-claim allowance is only `max(floor, 2 × interval)` = **20 min**
   (`cron/scheduler.py:823`, `:843`) — a 49.5-min sweep overruns its own allowance, saved
   only by the live-future check at `:848`. Raise the interval to ~30 min (or switch to
   run-after-completion). Also note the fire claim's **300 s TTL** (`cron/constants.py:9`)
   with a **60 s heartbeat** (`cron/scheduler.py:1149`, grace ×3 at `:1150`) is explicitly
   documented as outlived by real jobs (`cron/scheduler.py:607`, `:611`) — the claim cannot
   be the cross-run guard at these durations.
4. **Cache discovery responses** keyed `(keyword, location, offset)` with a 60–120 min TTL,
   shared across tenants — `/home/ubuntu/.hermes/profiles/*/workspace/discovery/_sweep_c.py`
   and `gates/effort_split.py`.
5. **Give each tenant its own scratch root.** Replace `/tmp` and `~/job-hunt-scratch`
   usage in `profiles/*/cron/jobs.json` prompts and workspace tools with
   `$HERMES_HOME/workspace/cache/scratch` (vishal already has `workspace/cache/scratch/`,
   28 files), and add a tmp reaper for the 29,073 leftovers.
6. **Batch the Sheets push** — one write per sweep instead of inline per-row pushes
   (`workspace/tools/jt.py:760`), with retry/backoff in
   `~/.hermes/scripts/push_trackers_to_sheets.py:183,303-304`.
7. **Add host admission control** — a cgroup per tenant, or a shared "browser budget" lock.
   Nothing today coordinates cross-tenant CPU/RAM/browser use, so N tenants contend
   blindly on 4 cores.

**Must move off-VM first (no in-VM change fixes these):**

- **LinkedIn guest API rate limit** — IP-bound. Needs rotating egress/proxy pool *outside*
  the box; caching (item 4) reduces but does not remove the wall.
- **Google Sheets quota** — per GCP *project*. Give each tenant its own project (or a
  queueing proxy) before tenant count approaches the ~300 writes/min project ceiling.
- **LLM provider limits and credit** — already the observed failure: nhung has 9 failed
  runs with `RuntimeError: HTTP 402: Insufficient Balance` and one
  `provider credential missing: 'deepseek'` in `profiles/nhung/cron/executions.db`.
  The prompts themselves budget "600 sub-agent runs" per the SUB-AGENT DISCIPLINE section,
  so provider throughput and cost are a first-class scaling constraint, not an afterthought.

### What cannot scale vertically here — stated plainly

- **4 OCPU / 24 GB is the Always Free A1 cap.** There is no vertical resize beyond it.
  Browsers are the irreducible cost: one headless chromium per tenant at **1.1–8.2 GB** and
  CPU-bound under load, with **8+2 sub-agents per sweep per tenant**. You cannot make that
  cheaper by tuning the VM, only by doing less work or capping concurrency.
- **A shared client IP cannot be un-shared by tuning.** The guest API limit is a property of
  egress, so it must leave the box.
- **Sheets quota is project-scoped**, so tenants sharing one GCP project are forever
  coupled on that axis; CPUs do not help.
- **Isolation is logical, not enforced.** One OS user + one `/tmp` + one outbound IP +
  shared tenant-blind tools (`push_trackers_to_sheets.py`, `jt.py`) mean a cross-tenant bug
  can touch the wrong candidate. Real isolation needs separate users/containers per tenant,
  which is a re-architecture, not a config line.

---

## 4. Cheap wins, with the estimated saving

| # | Win | Est. saving | Where |
|---|---|---|---|
| 1 | **Discovery response cache** — the same 92 queries are re-issued on every 10-min fire; a 60–120 min TTL serves them from disk | **−85–90 % guest-API volume** (92 → ~10–15 req/sweep) | `discovery/_sweep_c.py`, `_nl_discover.py` |
| 2 | **Share one discovery pass across tenants with the same keyword matrix** | **0 % today** — measured keyword jaccard is **0.00** (vishal 20 data-eng keywords vs nhung 20–24 AI-governance keywords, disjoint). Becomes free **−50 %** for the 3rd+ same-domain tenant once win 1 exists | `gates/effort_split.py`, prompts' DISCOVERY BUDGET sections |
| 3 | **Dedup employer/JD fetch across tenants** — the trackers already share **157 of ~1,002/1,039 companies (~15 %)**, e.g. `abbott`, `accenture the netherlands`, `atos`, `autodesk`, `amazon` | **~15 % of portal probes now**, more as tenants converge on the NL market | `workspace/discovery/*`, `workspace/runs/*` |
| 4 | **Reuse portal-probe outcomes across tenants** — "CAPTCHA / bot wall / broken form" is a property of the employer's portal, not of the candidate | **10–20 % of browser work** on the shared-employer overlap (directly cuts the CPU and tab-pressure ceilings) | portal-probe step in the pack prompts |
| 5 | **Batch tracker→Sheets writes** instead of inline per-row pushes | removes the only path whose call cardinality could approach the 300/min project quota | `workspace/tools/jt.py:760` |
| 6 | **Write the discovery table once per sweep** (the prompts already say "never carry an unwritten discovery list into the next run") | small CPU/disk, removes re-work | prompts (`vishal-job-hunt` ~line 306 / `nhung-job-hunt` ~line 178) |

**The one number to remember:** per-tenant marginal footprint is roughly
**1.5–2 GB RAM + ~1 core under load + a share of one client IP**, and the box has
**~6.7 GB of usable RAM and 4 cores** after the deliberate 6 GB ballast. That is
**~4–5 tenants nominal**, **~3 if any browser leaks tabs**, and the *first* wall to hit is
discovery's shared client IP plus the unbounded scheduler fan-out.
