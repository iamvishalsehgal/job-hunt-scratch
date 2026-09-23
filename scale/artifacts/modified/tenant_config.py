#!/usr/bin/env python3
"""tenant_config.py - the one place the ops scripts read tenant facts from.

WHY THIS FILE EXISTS
The deployment these scripts came from carried the candidate folder names and a
hardcoded /home/<operator> prefix inside every script, which is exactly why they were
never shippable. An ops script now takes --config (a tenant.yaml) and --workspace, and
everything else it needs - paths, mailbox patterns, thresholds, watchlists - is read
from that config here. Adding a tenant is adding a config file, not editing sixteen
scripts.

PyYAML is preferred and provisioning/provision_tenant.read_config_minimal is the
fallback, so behaviour matches the provisioner. The fallback reader cannot represent a
nested block (a list of mappings); when such a key is needed the accessor below says so
loudly and names PyYAML instead of inventing an empty value.

Exit codes shared by every ops script:
  0 ok | 1 the thing being watched is broken | 2 usage or config problem | 3 dependency missing

CLI (used by the bash scripts so they never parse YAML themselves):
  tenant_config.py --config TENANT.yaml [--workspace DIR] shell   # KEY=value assignments
  tenant_config.py --config TENANT.yaml [--workspace DIR] json    # resolved config
  tenant_config.py --config TENANT.yaml get ops.backup.keep       # one scalar
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shlex
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_USAGE = 2
EXIT_DEP = 3

# Mail classification defaults. Multilingual on purpose (a tenant may be hunting in any
# EU country), generic in the sense that matters: no candidate, employer or mailbox
# appears here. Override or extend per tenant with ops.mail_patterns.{inbox,otp,extra}.
DEFAULT_INBOX_PATTERN = (
    r"application|sollicitatie|interview|meeting invite|let.s chat|schedule|time confirmed|"
    r"next step|rejection|unfortunately|offer|assessment|uitgenodigd|gesprek|kennismaking|"
    r"intro call|your application|received your application|recruiter|teamtailor|ashbyhq|"
    r"greenhouse|pinpointhq|workable|lever\.co|video call|teams meeting|google meet|zoom|"
    r"phone screen|calendar invite|passcode|meeting id|verify|verification|bevestig|activat|"
    r"activeren|eenmalige|one.?time|pass.?code|security code|\botp\b|confirm your identity|"
    r"identity confirmation|set your password|inlogcode|candidate account"
)
DEFAULT_OTP_PATTERN = (
    r"verif|bevestig|activat|activeren|eenmalige|one.?time|pass.?code|passcode|security code|"
    r"\botp\b|confirm your identity|identity confirmation|set your password|inlogcode|"
    r"candidate account|bevestigingscode"
)


class OpsError(Exception):
    """A loud, operator-readable failure: message plus the exit code it should use."""

    def __init__(self, message: str, code: int = EXIT_USAGE):
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ config reading
def load_config(path: str | pathlib.Path) -> dict:
    p = pathlib.Path(str(path)).expanduser()
    if not p.is_file():
        raise OpsError(
            f"tenant config not found: {p} (pass --config or set JOBHUNT_CONFIG)"
        )
    text = p.read_text(encoding="utf-8")
    cfg = None
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load(text)
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from provisioning.provision_tenant import read_config_minimal  # noqa: PLC0415
        cfg = read_config_minimal(text)
    except Exception as exc:  # a malformed config must never be read as "empty"
        raise OpsError(f"{p} is not valid YAML: {exc}") from exc
    if not isinstance(cfg, dict):
        raise OpsError(f"{p} is not a tenant config (top level is {type(cfg).__name__})")
    if not str(get(cfg, "tenant.slug", "") or "").strip():
        raise OpsError(f"{p} is not a tenant config (tenant.slug is missing)")
    return cfg


def get(cfg: dict, dotted: str, default=None):
    """Fetch a dotted key, tolerating missing branches."""
    cur = cfg
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return default if cur is None else cur


def as_list(value) -> list:
    """Config lists arrive as lists (PyYAML), strings (hand written) or comma lists."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [v for v in value if v is not None and str(v).strip() != ""]
    if isinstance(value, str):
        parts = [v.strip() for v in value.replace(",", " ").split() if v.strip()]
        return parts
    return [value]


def as_int(value, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _need_mapping(value, dotted: str) -> dict:
    """A nested block the fallback reader cannot parse must say so, not read as {}."""
    if isinstance(value, dict):
        return value
    raise OpsError(
        f"{dotted} is not a mapping (got {type(value).__name__}). The fallback config "
        f"reader cannot parse nested blocks: install PyYAML for this tenant."
    )


# ------------------------------------------------------------------ paths
def resolve_workspace(cfg: dict, override: str = "") -> pathlib.Path:
    if override:
        ws = pathlib.Path(override).expanduser()
    else:
        raw = get(cfg, "paths.workspace", "~/hunts/{slug}")
        ws = pathlib.Path(str(raw).format(slug=get(cfg, "tenant.slug", ""))).expanduser()
    if str(ws) in {"", ".", "/"}:
        raise OpsError(f"refusing to use {ws} as a workspace")
    return ws


def require_workspace(cfg: dict, override: str = "") -> pathlib.Path:
    """A workspace that does not exist is a config problem, never an empty run."""
    ws = resolve_workspace(cfg, override)
    if not ws.is_dir():
        raise OpsError(
            f"workspace not found: {ws} (provision it, or pass --workspace)"
        )
    return ws


def state_dir(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    raw = get(cfg, "ops.state_dir", "")
    return pathlib.Path(str(raw)).expanduser() if raw else ws / "data" / "ops"


def usage_ledger(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    """This tenant's own model-usage ledger: what gates/model_budget.py appends a line to after each run.

    The default is mirrored in engine/gates/model_budget.py (LEDGER_REL), because the gate runs inside a
    provisioned workspace and cannot import this module. tests/test_model_budget.py asserts the two agree,
    so the operator's view and the gate's arithmetic can never end up describing different files.
    Override per tenant with ops.usage_ledger.
    """
    raw = get(cfg, "ops.usage_ledger", "")
    return pathlib.Path(str(raw)).expanduser() if raw else ws / "data" / "usage.jsonl"


def row_store_path(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    """Where the tracker's ROWS live: python source the gates can parse with no credentials.

    This is the source the sheet is built from. It is engine data, never shown to a person, and
    it replaced the workbook as the thing the engine reads and writes.
    """
    raw = get(cfg, "ops.tracker_source", "")
    return pathlib.Path(str(raw)).expanduser() if raw else ws / "build_tracker.py"


def render_path(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    """Where the DERIVED workbook goes, if something asks for one: under output/, never at the root.

    Only the CV pipeline needs a file path, and the render is disposable, so it is never a
    maintained artefact and never lives next to the row store.
    """
    raw = get(cfg, "ops.tracker_render", "")
    return pathlib.Path(str(raw)).expanduser() if raw else ws / "output" / "tracker-render.xlsx"


def backups_dir(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    raw = get(cfg, "ops.backup.dir", "")
    return pathlib.Path(str(raw)).expanduser() if raw else ws / "data" / "backups"


def home_root(override: str = "") -> pathlib.Path:
    return pathlib.Path(override).expanduser() if override else pathlib.Path.home()


def hermes_home(cfg: dict, home: pathlib.Path) -> pathlib.Path:
    """The Hermes profile directory that belongs to THIS tenant and no other."""
    profile = profile_name(cfg)
    if profile in {"", "default"}:
        return home / ".hermes"
    return home / ".hermes" / "profiles" / profile


def hermes_base(cfg: dict, home: pathlib.Path) -> pathlib.Path:
    return home / ".hermes"


def google_token(cfg: dict, home: pathlib.Path, profile_dir: pathlib.Path) -> pathlib.Path:
    """Where the OAuth token lives: explicit config first, then the profile, then the root.

    A token is a secret-shaped file, so it is never created here - only located. The
    fallback order matters because a tenant profile keeps its own consent, while a
    single-tenant host keeps one at the root of its Hermes home.
    """
    raw = str(get(cfg, "ops.google.token", "") or "")
    if raw:
        return pathlib.Path(raw).expanduser()
    for cand in (profile_dir / "google_token.json", home / ".hermes" / "google_token.json"):
        if cand.exists():
            return cand
    return home / ".hermes" / "google_token.json"


# ------------------------------------------------------------------ knobs
def profile_name(cfg: dict) -> str:
    """The Hermes profile this tenant owns. `{slug}` is rendered, never left literal."""
    raw = str(get(cfg, "paths.profile", "") or get(cfg, "tenant.slug", ""))
    return raw.format(slug=get(cfg, "tenant.slug", ""))


def mail_account(cfg: dict) -> str:
    return str(get(cfg, "ops.mail.account", ""))


def mail_bin(cfg: dict) -> str:
    """The env override wins: it is how a caller (or a test) pins the mailbox tool."""
    return os.environ.get("MAIL_BIN", "") or str(get(cfg, "ops.mail.bin", ""))


def mail_page_size(cfg: dict) -> int:
    return as_int(get(cfg, "ops.mail.page_size", 60), 60)


def mail_pattern(cfg: dict, name: str) -> str:
    base = DEFAULT_OTP_PATTERN if name == "otp" else DEFAULT_INBOX_PATTERN
    override = str(get(cfg, f"ops.mail_patterns.{name}", "") or "").strip()
    extra = str(get(cfg, "ops.mail_patterns.extra", "") or "").strip()
    pat = override or base
    return f"{pat}|{extra}" if extra else pat


def seen_file(cfg: dict, ws: pathlib.Path) -> pathlib.Path:
    raw = get(cfg, "ops.mail.seen_file", "")
    return pathlib.Path(str(raw)).expanduser() if raw else state_dir(cfg, ws) / "mail_seen.txt"


def machine_line(name: str, **fields) -> str:
    """The single machine-readable line every ops script ends with.

    One line, key=value, parseable with grep/sed by the cron prompt and by the
    watchdog. `status` is always the first field so `grep -o 'status=[a-z]*'` works on
    every script alike; values are never quoted, so anything with a space is normalised.
    """
    bits = [name]
    for key in ["status"] + sorted(k for k in fields if k != "status"):
        val = fields[key]
        val = str(val).replace("\n", " ").replace(" ", "_").strip()
        bits.append(f"{key}={val}" if val != "" else f"{key}=-")
    return " ".join(bits)


# ------------------------------------------------------------------ CLI
def _shell_dump(cfg: dict, ws: pathlib.Path, cfg_path: pathlib.Path, opts: dict | None = None) -> str:
    opts = opts or {}
    home = home_root(opts.get("home_root", ""))
    ph = hermes_home(cfg, home)
    values = {
        "CONFIG": str(cfg_path),
        "HOME_ROOT": str(home),
        "TENANT_SLUG": str(get(cfg, "tenant.slug", "")),
        "PROFILE": profile_name(cfg),
        "PROFILE_DIR": str(ph),
        "HERMES_HOME": str(hermes_base(cfg, home)),
        "WORKSPACE": str(ws),
        "STATE_DIR": str(state_dir(cfg, ws)),
        "USAGE_LEDGER": str(usage_ledger(cfg, ws)),
        "ROW_STORE": str(row_store_path(cfg, ws)),
        "TRACKER_RENDER": str(render_path(cfg, ws)),
        "BACKUP_DIR": str(backups_dir(cfg, ws)),
        "BACKUP_KEEP": str(as_int(get(cfg, "ops.backup.keep", 6), 6)),
        "MAIL_ACCOUNT": mail_account(cfg),
        "MAIL_BIN": mail_bin(cfg),
        "MAIL_PAGE_SIZE": str(mail_page_size(cfg)),
        "MAIL_SEEN": str(seen_file(cfg, ws)),
        "PATTERN_INBOX": mail_pattern(cfg, "inbox"),
        "PATTERN_OTP": mail_pattern(cfg, "otp"),
        "TRACKER_PYTHON": str(get(cfg, "ops.tracker_python", "") or ""),
        "WATCH_HEARTBEATS": " ".join(v for v in as_list(get(cfg, "ops.watch.heartbeats"))) or "",
        "WATCH_UNITS": " ".join(v for v in as_list(get(cfg, "ops.watch.units"))) or "",
        "WATCH_EXECUTIONS_DB": str(get(cfg, "ops.watch.executions_db", "") or ph / "cron" / "executions.db"),
        "GOOGLE_API_LIB": str(get(cfg, "ops.google.api_lib", "") or os.environ.get("GOOGLE_API_LIB", "")),
        "GOOGLE_TOKEN": str(google_token(cfg, home, ph)),
    }
    for k in (opts.get("extra") or {}):
        values[k] = str(opts["extra"][k])
    return "\n".join(f"{k}={shlex.quote(v)}" for k, v in values.items())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tenant_config.py", description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=os.environ.get("JOBHUNT_CONFIG", "") or str(ROOT / "config" / "tenant.yaml"))
    ap.add_argument("--workspace", default="")
    ap.add_argument("--home-root", default="",
                    help="home directory the profile paths hang off (default: $HOME). "
                         "A fresh host or a test harness needs this to be explicit.")
    ap.add_argument("action", choices=["shell", "json", "get"])
    ap.add_argument("key", nargs="?")
    a = ap.parse_args(argv)
    try:
        cfg = load_config(a.config)
        ws = resolve_workspace(cfg, a.workspace)
        if a.action == "shell":
            print(_shell_dump(cfg, ws, pathlib.Path(a.config).expanduser(),
                              {"home_root": a.home_root}))
        elif a.action == "json":
            print(json.dumps({"config": str(pathlib.Path(a.config).expanduser()),
                              "workspace": str(ws), "values": _json_values(cfg, ws)}, indent=1))
        else:
            if not a.key:
                raise OpsError("get needs a dotted key")
            print(get(cfg, a.key, ""))
    except OpsError as exc:
        print(f"tenant_config: {exc}", file=sys.stderr)
        return exc.code
    return EXIT_OK


def _json_values(cfg: dict, ws: pathlib.Path) -> dict:
    return {
        "tenant": str(get(cfg, "tenant.slug", "")),
        "workspace": str(ws),
        "state_dir": str(state_dir(cfg, ws)),
        "usage_ledger": str(usage_ledger(cfg, ws)),
        "row_store": str(row_store_path(cfg, ws)),
        "tracker_render": str(render_path(cfg, ws)),
        "backups": str(backups_dir(cfg, ws)),
        "mail_account": mail_account(cfg),
        "inbox_pattern": mail_pattern(cfg, "inbox"),
        "otp_pattern": mail_pattern(cfg, "otp"),
    }


if __name__ == "__main__":
    sys.exit(main())