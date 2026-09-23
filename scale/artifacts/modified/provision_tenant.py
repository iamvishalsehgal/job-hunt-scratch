#!/usr/bin/env python3
"""provision_tenant.py - turn a tenant.yaml into a running hunt.

Steps (all idempotent):
  1. validate the config (countries inside the EU scope, salary rules consistent, plan exists)
  2. create the candidate workspace and install what its prompts name: the row store
     (build_tracker.py from engine/build_tracker.template.py), the gates, and tools/jt.py,
     tools/verify_tracker.py, tools/batch_manifest.py and tools/apply_email.py
  3. write the scope file (eu_scope.json) from the tenant's country tiers
  4. create the Hermes profile for the tenant and enable linger
  5. create the cron jobs from engine/cron/jobs.template.json, with every placeholder rendered from
     the config and the cadence taken from the tenant's own schedule block
  6. write usage/<slug>.jsonl so metering starts on the first run
  7. print a checklist of what still needs the human (mail app password, bot token, licence key)

  python3 provisioning/provision_tenant.py --config config/tenant.yaml [--dry-run]

The engine never guesses a credential: anything missing is reported, not invented.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "GR", "HU", "IE", "IT",
    "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}
REQUIRED_PLANS = {p["id"] for p in json.loads((ROOT / "pricing.yaml").read_text(encoding="utf-8"))["plans"]}

# What a provisioned workspace has to hold, as (path in this repo, path inside the workspace).
# The job prompts call tools/jt.py, tools/batch_manifest.py, tools/prune_rejected.py and the row store
# build_tracker.py, and
# jt.py itself looks for tools/verify_tracker.py and tools/apply_email.py first, so a workspace
# that is missing any of these is a workspace whose documented commands cannot run.
WORKSPACE_INSTALLS = (
    ("engine/tools/jt.py", "tools/jt.py"),
    ("engine/tools/batch_manifest.py", "tools/batch_manifest.py"),
    ("engine/tools/verify_tracker.py", "tools/verify_tracker.py"),
    # the rejected-docs rule: jt.py calls it after a row write, so it must exist in the workspace
    ("engine/tools/prune_rejected.py", "tools/prune_rejected.py"),
    ("engine/notify/notify.py", "tools/notify.py"),
    ("engine/notify/send_alert.py", "tools/send_alert.py"),
    ("engine/notify/apply_email.py", "tools/apply_email.py"),
    ("engine/build_tracker.template.py", "build_tracker.py"),
)

# The sweep prompt names these with an exact path and one line saying when to read them. They hold the
# static guidance that used to sit in the prompt itself and was re-sent on every turn of every sweep
# (see engine/tools/prompt_playbook.py). Every file here has to land in the workspace, or the prompt
# points at a path that does not exist.
WORKSPACE_REFERENCES = tuple(sorted(q.name for q in (ROOT / "engine" / "references").glob("*.md")))
GATE_FILES = ("eu_scope_gate.py", "effort_split.py", "dutch_gate.py", "row_gate.py",
              "ping_gate.py", "email_guard.py", "otp_fetch.py", "language_gate.py",
              "interview_backoff.py",
              "model_budget.py")

# Which config key sets which job's cadence. Every key of `schedule` in the tenant config is
# consumed here; the template value is only the fallback.
SCHEDULE_KEYS = {"sweep": "sweep", "mailbox": "mailbox", "backup": "backup",
                 "sheets_sync": "sheets_sync"}


# ---------------------------------------------------------------- a tiny YAML subset reader
def read_config(path: pathlib.Path) -> dict:
    """Parse the tenant config. Uses PyYAML when available, else a minimal reader for our shape."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        return read_config_minimal(text)


def read_config_minimal(text: str) -> dict:
    """The fallback reader, exposed so it can be tested even where PyYAML is installed.

    It has to agree with PyYAML on our own example config, because it is the reader a customer host without
    PyYAML actually runs. Traps it handles, each of which shipped a wrong value once:

      * a trailing ` # comment` landing inside the value (turning a list into a string, a salary floor into
        a str);
      * a key whose ONLY value is an aligned comment (`sheets:   # the sheet IS the tracker`) being stored as
        that comment text instead of opening a block - which hid delivery.sheets and rendered every tracker
        link empty on hosts without PyYAML;
      * list numbers staying strings, so `min(ask_range) < target_floor` raised TypeError;
      * a list of mappings (`watchlists.agencies`) raising `TypeError: list indices must be integers`;
      * a flow mapping inside a list (`- { name: English, level: fluent }`);
      * a block scalar (`>` folded, `|` literal) becoming the literal ">" and dropping its text.

    A reader that dies on valid YAML of our own shape is worse than a loud refusal: the ops scripts run on
    hosts where PyYAML is not installed at all.
    """
    data: dict = {}
    stack = [(-1, data)]
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            item = line[2:]
            if isinstance(parent, list):
                if item.startswith("{") and item.endswith("}"):
                    parent.append(_flow_mapping(item))
                elif ":" in item and not item.startswith("["):
                    # `- name: X` opens a BLOCK mapping item: the keys indented under it belong to
                    # this item, not to the list, so push the mapping and keep the list underneath.
                    mapping: dict = {}
                    key, _, val = item.partition(":")
                    mapping[key.strip()] = _scalar(val.strip())
                    parent.append(mapping)
                    stack.append((indent, mapping))
                else:
                    parent.append(_scalar(item))
            continue
        if ":" not in line:
            continue
        target = parent
        if isinstance(parent, list):
            # A bare key under a list continues its last mapping item.
            if not (parent and isinstance(parent[-1], dict)):
                continue
            target = parent[-1]
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if _strip_inline_comment(val).strip() == "":
            nxt = _peek_block(raw, lines[i:])
            container = [] if nxt.startswith("- ") else {}
            target[key] = container
            stack.append((indent, container))
        elif val.split()[0] in (">", "|", ">-", "|-", ">+", "|+"):
            # A block scalar: every following line indented deeper than the key belongs to the value.
            style = val.split()[0]
            body, i = _block_scalar(lines, i, indent, folded=style.startswith(">"))
            target[key] = body
        else:
            target[key] = _scalar(val)
    return data


def _block_scalar(lines, i: int, key_indent: int, folded: bool) -> tuple:
    """The text of a `>` / `|` block, and the index just past it.

    Folded style turns a line break into a space - EXCEPT before a line indented deeper than the block's
    first content line: there the break is literal and the extra indentation stays. Content is therefore
    `raw[base:]`, not the stripped line; the example config's work-authorisation template relies on both
    rules, and getting either wrong mangles the licence text a prompt states.
    """
    block = []
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            block.append((None, ""))
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent <= key_indent:
            break
        block.append((indent, raw))
        i += 1
    while block and not block[-1][1].strip():
        block.pop()
    if not block:
        return "", i
    base = next(indent for indent, raw in block if raw.strip())
    if not folded:
        return "\n".join(raw[base:] for _, raw in block if raw.strip()) + "\n", i
    out = ""
    for indent, raw in block:
        if not raw.strip():
            out += "\n"
        elif not out:
            out += raw[base:].rstrip()
        elif indent is not None and indent > base:
            out += "\n" + raw[base:].rstrip()
        else:
            out += " " + raw[base:].strip()
    return (out + "\n" if out.strip() else ""), i


def _flow_mapping(item: str) -> dict:
    """`{ name: English, level: fluent }` as a dict. Nested flow is not claimed."""
    out: dict = {}
    for pair in item[1:-1].split(","):
        if ":" not in pair:
            continue
        k, _, v = pair.partition(":")
        out[k.strip().strip('"').strip("'")] = _scalar(v.strip())
    return out


def _peek_block(current: str, rest) -> str:
    """The first non-blank line after `current`, which decides whether a block is a list or a mapping."""
    for line in rest:
        if not line.strip():
            continue
        return line.strip()
    return ""


def _strip_inline_comment(v: str) -> str:
    """Drop a trailing ` # comment` from a value, ignoring a # inside quotes or a URL fragment."""
    quote = ""
    for i, ch in enumerate(v):
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            continue
        if ch == "#" and (i == 0 or v[i - 1].isspace()):
            return v[:i].rstrip()
    return v.rstrip()


def _scalar(v: str):
    v = _strip_inline_comment(v).strip().strip('"').strip("'")
    if v.startswith("[") and v.endswith("]"):
        return [_coerce(x.strip().strip('"').strip("'")) for x in v[1:-1].split(",") if x.strip()]
    return _coerce(v)


def _coerce(v: str):
    if v.lower() in {"true", "false"}:
        return v.lower() == "true"
    if v.lower() in {"null", "none", "~"}:
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def install_workspace_files(ws: pathlib.Path, dry: bool = False) -> list:
    """Copy the gates, the row store and the tools into the workspace. Returns what landed (or would).

    One list, one place: a tool a prompt names, or jt.py looks for, has to be installed by provisioning,
    or the job that calls it fails on a host nobody has hand-tuned.
    """
    installed = []
    sources = [(ROOT / "engine" / "gates" / n, ws / "gates" / n) for n in GATE_FILES]
    sources += [(ROOT / rel, ws / target) for rel, target in WORKSPACE_INSTALLS]
    sources += [(ROOT / "engine" / "references" / n, ws / "references" / n)
                for n in WORKSPACE_REFERENCES]
    for src, dst in sources:
        if not src.exists():
            print(f"  WARN {src} is missing from this checkout; {dst} cannot be installed")
            continue
        if dry:
            print(f"  cp {src} -> {dst}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if dst.suffix in {".py", ".sh"}:
                dst.chmod(0o755)
        installed.append(dst)
    return installed


# ---------------------------------------------------------------- validation
def validate(cfg: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    t = cfg.get("tenant", {})
    c = cfg.get("candidate", {})
    g = cfg.get("targeting", {})
    countries = g.get("countries", {}) or {}
    allc = list(countries.get("primary", []) or []) + list(countries.get("secondary", []) or []) \
        + list(countries.get("rotation", []) or [])
    if not t.get("slug"):
        errors.append("tenant.slug is required")
    if not c.get("email"):
        errors.append("candidate.email is required (used for portal accounts and mail)")
    bad = [cc for cc in allc if cc not in EU27]
    if bad:
        errors.append(f"countries outside the EU are not supported: {bad} (EU-only scope)")
    if not countries.get("primary"):
        errors.append("targeting.countries.primary needs at least one country")
    share = (g.get("effort_split") or {}).get("primary_share", 0.8)
    if not 0.5 <= share <= 1.0:
        warnings.append(f"effort_split.primary_share={share} is unusual (expected 0.8)")
    salary = cfg.get("salary", {}) or {}
    if salary.get("target_floor") and salary.get("ask_range"):
        lo = min(salary["ask_range"])
        if lo < salary["target_floor"]:
            errors.append("salary.ask_range starts below salary.target_floor")
    plan = (cfg.get("billing", {}) or {}).get("plan", "starter")
    if plan not in REQUIRED_PLANS:
        errors.append(f"billing.plan {plan!r} is not one of {sorted(REQUIRED_PLANS)}")
    if (cfg.get("delivery", {}) or {}).get("email_read_only") is not True:
        errors.append("delivery.email_read_only must be true: the engine never sends mail")
    sheets_id = str(((cfg.get("delivery") or {}).get("sheets") or {}).get("id", "") or "")
    if not sheets_id:
        warnings.append("delivery.sheets.id is empty: every prompt's tracker link would be broken")
    if (cfg.get("delivery", {}) or {}).get("notifications", {}).get("outbound_only") is not True:
        warnings.append("delivery.notifications.outbound_only=false: inbound polling is not supported")
    return errors, warnings


# ---------------------------------------------------------------- provisioning
def workspace_for(cfg: dict) -> pathlib.Path:
    slug = cfg["tenant"]["slug"]
    raw = (cfg.get("paths", {}) or {}).get("workspace", "~/hunts/{slug}").format(slug=slug)
    return pathlib.Path(os.path.expanduser(raw))


def carry_budget_dial(cfg: dict, ws: pathlib.Path, dry: bool = False) -> str:
    """Put the tenant's budget dial where the unattended sweep can read it, and start its ledger.

    The workspace's own dial files (notify.json / config.json - the two names the runtime already reads:
    engine/notify/apply_email.py) are what a cron run can see. The tenant config lives in the operator's
    checkout, which a customer host does not have, so a provisioned account whose dial never travelled
    would fall back to the gate's built-in default and say so on every single sweep. The ledger is
    created empty here for the same reason provisioning touches usage/<slug>.jsonl: metering starts on
    the first run rather than on the first successful write.

    Never fatal: the gate degrades to a default it can see and reports it, which beats a provisioning
    run that fails over a dial.
    """
    budget = cfg.get("budget") if isinstance(cfg.get("budget"), dict) else {}
    if dry:
        return f"budget dial: {'would be carried' if budget else 'nothing to carry (the gate defaults apply)'}"
    try:
        sys.path.insert(0, str(ROOT / "engine" / "gates"))
        import model_budget  # noqa: PLC0415

        path = (model_budget.write_budget(ws, daily_usd=budget.get("daily_usd"),
                                          on_exceed=budget.get("on_exceed"),
                                          throttle_rate=budget.get("throttle_rate"))
                if budget else None)
        ledger = model_budget.ledger_path(ws)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.touch()
        return f"budget dial: {path if path else 'none in the config, the gate defaults apply'}; ledger {ledger}"
    except Exception as e:  # a dial that could not travel must not stop the account being created
        return f"WARN the budget dial could not be carried into the workspace: {e}"


def write_scope(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    g = cfg["targeting"]
    countries = g.get("countries", {})
    langs = (cfg.get("language_gate", {}) or {}).get("local_languages", {})
    scope = {
        "_comment": "Generated by provisioning/provision_tenant.py from config/tenant.yaml. "
                    "EU-only: the gates refuse anything outside the EU member states.",
        "core": (countries.get("primary") or ["NL"])[0],
        "manual_apply_countries": [],
        "tiers": {"1": {"countries": countries.get("secondary", [])},
                  "2": {"countries": countries.get("rotation", [])}},
        "local_languages": langs,
        "rotation_state_file": str(ws / "discovery" / "rotation.json"),
    }
    p = ws / "eu_scope.json"
    p.write_text(json.dumps(scope, indent=1) + "\n", encoding="utf-8")
    return p


def provision(cfg: dict, dry: bool) -> int:
    slug = cfg["tenant"]["slug"]
    ws = workspace_for(cfg)
    # Derive the profile name here as well as further down: the ops-script install below needs it,
    # and python scoping would otherwise make the later assignment an UnboundLocalError here.
    profile_name = (cfg.get("paths", {}) or {}).get("profile", slug).format(slug=slug)
    profile_is_default = (profile_name == "default")
    steps = []
    for sub in ("gates", "tools", "data", "applications", "interviews", "discovery", "output"):
        steps.append(ws / sub)
    for d in steps:
        if dry:
            print(f"  mkdir -p {d}")
        else:
            d.mkdir(parents=True, exist_ok=True)

    install_workspace_files(ws, dry)

    # Create the profile first: the ops-script install below creates ~/.hermes/profiles/<profile>/,
    # and the scheduler refuses to create a profile whose directory already exists without an
    # identity file. Order is load-bearing here, not cosmetic.
    hermes_bin = shutil.which("hermes") or "hermes"
    if not profile_is_default:
        identity = pathlib.Path(os.path.expanduser(f"~/.hermes/profiles/{profile_name}/config.yaml"))
        if identity.exists():
            print(f"  profile {profile_name}: exists")
        elif dry:
            print(f"  hermes profile create {profile_name}")
        else:
            r = subprocess.run([hermes_bin, "profile", "create", profile_name],
                               capture_output=True, text=True)
            print(f"  profile {profile_name}: created={identity.exists()} rc={r.returncode}")
            if not identity.exists():
                print(f"  ERROR could not create the profile {profile_name!r}: "
                      f"{(r.stderr or r.stdout).strip()[:200]}")
                return 1

    # the ops scripts: a monitor name and a --script name both resolve here, so a fresh host needs
    # them installed before its jobs are created. Named profiles get their own scripts dir (that is
    # what the live deployment uses), the default profile shares ~/.hermes/scripts.
    scripts_dir = pathlib.Path(os.path.expanduser(
        "~/.hermes/scripts" if profile_is_default else f"~/.hermes/profiles/{profile_name}/scripts"))
    for src in sorted((ROOT / "engine" / "scripts").glob("*")):
        if not src.is_file():
            continue
        dst = scripts_dir / src.name
        if dry:
            print(f"  cp {src} -> {dst}")
        else:
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if src.suffix in {".sh", ".py"}:
                dst.chmod(0o755)

    sp = write_scope(cfg, ws) if not dry else ws / "eu_scope.json"
    print(f"  scope file: {sp}")
    print(f"  {carry_budget_dial(cfg, ws, dry)}")

    # Hermes profile + cron jobs. The profile MUST exist first: every cron create against a missing
    # profile returns rc=1, and the run would finish "successfully" having created nothing.
    profile = profile_name
    hermes = shutil.which("hermes") or "hermes"
    jobs = json.loads((ROOT / "engine" / "cron" / "jobs.template.json").read_text(encoding="utf-8"))
    for job in jobs:
        cmd = build_cron_command(job, cfg, ws, profile, hermes)
        name, schedule = rendered_name(job, cfg, ws), job_schedule(job, cfg)
        prompt = job_prompt_len(job, cfg, ws)
        if dry:
            print(f"  cron create {name} ({schedule}) prompt={prompt}c "
                  f"script={job.get('script') or '-'} no-agent={job.get('no_agent') or '-'} "
                  f"monitor={job.get('monitor_script') or '-'}")
        else:
            r = subprocess.run(cmd, capture_output=True, text=True)
            print(f"  cron {name}: rc={r.returncode} "
                  f"{(r.stdout + r.stderr).strip().splitlines()[-1][:80] if (r.stdout + r.stderr).strip() else ''}")

    usage = ROOT / "usage"
    usage.mkdir(exist_ok=True)
    (usage / f"{slug}.jsonl").touch()

    print("\nstill needs the human:")
    print("  - mail app password in ~/.config/himalaya/config.toml (IMAP only, no smtp keys)")
    print("  - Telegram bot token in ~/.hermes/.telegram-token (mode 600, outbound-only)")
    print("  - licence key in config/tenant.yaml when billing is live "
          f"(plan {cfg.get('billing', {}).get('plan', 'starter')})")
    print("  - profile gateway: hermes gateway install (per profile)")
    return 0


def rendered_name(job: dict, cfg: dict, ws: pathlib.Path) -> str:
    """A job name with its placeholders rendered: `jane-doe-backup`, not a literal `{{SLUG}}-backup`."""
    return render_prompt(job["name"], cfg, ws)


def job_prompt_len(job: dict, cfg: dict, ws: pathlib.Path) -> int:
    """How many characters of prompt this job gets (0 for a script-only job)."""
    if job.get("script") or job.get("no_agent"):
        return 0
    return len(render_prompt(job["prompt"], cfg, ws))


def job_schedule(job: dict, cfg: dict) -> str:
    """A job's cadence: the tenant's own `schedule` block wins, the template value is the default.

    config/tenant.example.yaml documents `schedule` as the cost dial and the dashboard shows the same
    value, so provisioning has to create the jobs with the cadence the tenant actually set.
    """
    key = SCHEDULE_KEYS.get(job.get("role", ""))
    if key:
        value = (cfg.get("schedule") or {}).get(key)
        if value:
            return str(value)
    return job["schedule"]


def build_cron_command(job: dict, cfg: dict, ws: pathlib.Path, profile: str, hermes: str) -> list:
    """The `hermes cron create` line for one template job, fully rendered.

    A script-only job is run by the scheduler, not by a model: it takes no prompt, and its stdout is
    the delivery. Everything else gets the rendered prompt.
    """
    script = job.get("script") or ""
    no_agent = bool(job.get("no_agent")) or bool(script)
    prompt = "" if no_agent else render_prompt(job["prompt"], cfg, ws)
    cmd = [hermes]
    if profile != "default":
        cmd += ["-p", profile]
    cmd += ["cron", "create", job_schedule(job, cfg)]
    if prompt:
        cmd += [prompt]
    cmd += ["--name", rendered_name(job, cfg, ws), "--deliver", "local", "--paused",
            "--paused-reason", "provisioned - resume when the tenant confirms"]
    if script:
        cmd += ["--script", script]
        if job.get("no_agent"):
            cmd += ["--no-agent"]
    if job.get("monitor_script"):
        cmd += ["--monitor-script", job["monitor_script"]]
    return cmd


_FAILED_APPLY_ROUTE_TEXT = {
    "hr_email": (
        "  - FAILED AUTO-APPLY -> EMAIL HR. Run\n"
        "      python3 {{WORKSPACE}}/tools/jt.py apply-email --pack {{WORKSPACE}}/applications/<slug> \\\n"
        "        --company \"<company>\" --role \"<role>\" --portal-url \"<apply url>\"\n"
        "    It sends the tailored cv.pdf + cover-letter.pdf once per role and records the row (Emailed); it\n"
        "    refuses a duplicate, an early follow-up or a reply. At most ONE follow-up later, when due; never\n"
        "    reply to an employer - what they ask is pinged to the candidate."),
    "telegram_apply_link": (
        "  - FAILED AUTO-APPLY -> SEND THE CANDIDATE THE LINK. Attach the documents as files (send_alert.py),\n"
        "    put the apply URL in the message text, then record the row BROWSER NEEDED with that URL:\n"
        "      python3 {{WORKSPACE}}/tools/send_alert.py --kind action \\\n"
        "        --text \"<company> - <role>: apply here <apply url>\" \\\n"
        "        --attach {{WORKSPACE}}/applications/<slug>/cv.pdf \\\n"
        "                 {{WORKSPACE}}/applications/<slug>/cover-letter.pdf \\\n"
        "                 {{WORKSPACE}}/applications/<slug>/jd.md\n"
        "    NEVER email an employer from this candidate's account: their email channel is off."),
}


def _failed_apply_route(cfg: dict, workspace) -> str:
    """The paragraph a prompt carries for a role the engine could not apply to automatically.

    The tenant chooses with `delivery.failed_apply_route`: `hr_email` (the engine emails HR, so the
    application-email channel must be enabled) or `telegram_apply_link` (the candidate gets the link and the
    documents and applies themselves). Both keep the same primary instruction - apply automatically first.
    """
    route = str(((cfg.get("delivery") or {}).get("failed_apply_route") or "telegram_apply_link")).strip().lower()
    if route not in ("hr_email", "telegram_apply_link"):
        raise ValueError(f"delivery.failed_apply_route must be hr_email or telegram_apply_link, not {route!r}")
    # the workspace is substituted here: render_prompt makes ONE pass, so a nested placeholder
    # would survive into the live prompt and the guard would refuse it.
    return _FAILED_APPLY_ROUTE_TEXT[route].replace("{{WORKSPACE}}", str(workspace))


def render_prompt(template: str, cfg: dict, ws: pathlib.Path) -> str:
    c = cfg["candidate"]
    g = cfg["targeting"]
    s = cfg.get("salary", {}) or {}
    countries = g.get("countries", {})
    repl = {
        "{{SLUG}}": cfg["tenant"]["slug"],
        "{{FULL_NAME}}": c.get("full_name", ""),
        "{{EMAIL}}": c.get("email", ""),
        "{{PHONE}}": c.get("phone", ""),
        "{{CITY}}": c.get("city", ""),
        "{{WORKSPACE}}": str(ws),
        "{{FAILED_APPLY_ROUTE}}": _failed_apply_route(cfg, ws),
        "{{SHEET_ID}}": str(((cfg.get("delivery") or {}).get("sheets") or {}).get("id", "")),
        "{{SHEET_URL}}": ("https://docs.google.com/spreadsheets/d/"
                          + str(((cfg.get("delivery") or {}).get("sheets") or {}).get("id", ""))
                          + "/edit") if ((cfg.get("delivery") or {}).get("sheets") or {}).get("id")
                         else "",
        "{{PRIMARY}}": (countries.get("primary") or [""])[0],
        "{{SECONDARY}}": ", ".join(countries.get("secondary", [])),
        "{{ROTATION}}": ", ".join(countries.get("rotation", [])),
        "{{ROLES}}": ", ".join(g.get("roles", [])),
        "{{PRIMARY_SHARE}}": str((g.get("effort_split") or {}).get("primary_share", 0.8)),
        "{{CURRENT_GROSS}}": str(s.get("current_gross", "")),
        "{{TARGET_FLOOR}}": str(s.get("target_floor", "")),
        "{{LEGAL_FLOOR}}": str(s.get("legal_floor", "")),
        "{{CURRENT_EMPLOYER}}": str(c.get("current_employer", "")),
        "{{DEGREE_INSTITUTION}}": str(c.get("degree_institution", "")),
        "{{LINKEDIN}}": str(c.get("linkedin", "")),
        "{{GITHUB}}": str(c.get("github", "")),
        "{{ASK_RANGE}}": "-".join(str(x) for x in s.get("ask_range", [])),
        "{{HARD_CAP_YEARS}}": str(g.get("hard_cap_years", 6)),
    }
    for k, v in repl.items():
        template = template.replace(k, v)
    left = sorted(set(re.findall(r"\{\{[A-Za-z_]+\}\}", template)))
    if left:
        # A placeholder with no mapping survives into a live prompt as literal text, which has already
        # shipped once. Fail loudly here instead: that is a template bug, not a tenant's mistake.
        raise ValueError("unrendered placeholder(s) " + ", ".join(left)
                         + " in a job template: map them in render_prompt or drop them from the template")
    return template


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = read_config(pathlib.Path(a.config).expanduser())
    errors, warnings = validate(cfg)
    for w in warnings:
        print("WARN", w)
    if errors:
        for e in errors:
            print("ERROR", e)
        return 2
    print(f"provisioning tenant {cfg['tenant']['slug']} "
          f"({'dry run' if a.dry_run else 'live'})")
    return provision(cfg, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
