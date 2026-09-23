#!/usr/bin/env python3
"""Deploy the employer-email channel into the live candidate workspaces. Additive edits ONLY.

1. tools/apply_email.py        : the new module (a copy of the engine file).
2. tools/notify.py             : insert the human-wording guards (the deployed copy predates them).
3. tools/jt.py                 : insert the apply-email subcommand + the routing gate, without
                                 touching the parts of the deployed copy that differ from the engine.
4. notify.json                 : the application_email block (vishal enabled, everyone else disabled).
"""
import json
import pathlib
import shutil
import sys

REPO = pathlib.Path("/home/ubuntu/wt/appmail")
PROFILES = pathlib.Path.home() / ".hermes" / "profiles"
ENABLED = {"vishal": True, "nhung": False}
AVAILABILITY = {"vishal": "I am available from 4 December 2026.", "nhung": ""}
FROM_NAME = {"vishal": "Vishal Sehgal", "nhung": "Nhung Trang Giap"}


def edit(path: pathlib.Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and label.startswith("already"):
        print(f"   {label}: present")
        return
    if text.count(old) != 1:
        raise SystemExit(f"FAILED {label}: anchor found {text.count(old)}x in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"   {label}: inserted")


def deploy_notify_py(tools: pathlib.Path) -> None:
    """Add the automation-wording guards the alert module gained after this copy was made."""
    path = tools / "notify.py"
    block = '''# --------------------------------------------------------------------------- human wording
# The alert channel's rule, in one place: an email must NEVER describe itself as automated.
AUTOMATION_WORDING = re.compile(
    r"(?:\\bautomated\\b|\\bautomatic\\b|\\bautomatically\\b|\\bautomation\\b|\\bautomat(?:ed|ic) (?:message|email|notification|alert|system|reply)\\b"
    r"|\\bauto[- ]?(?:generated|sent|message|notification|email|reply|reminder|mailer)\\b"
    r"|\\bsystem[- ]generated\\b|\\bmachine[- ]generated\\b|\\bai[- ]generated\\b|\\bai[- ]written\\b"
    r"|\\bgenerated (?:automatically|by (?:an? )?(?:ai|bot|machine|robot|system|script|program))\\b"
    r"|\\b(?:ro)?bot(?:ic|ically)?\\b|\\bchatbot\\b|\\bvirtual assistant\\b|\\bautomated assistant\\b"
    r"|\\bdo(?: not|n't) reply\\b|\\bno[\\s_-]?reply\\b|\\bnoreply\\b|\\bdo[\\s_-]?not[\\s_-]?reply\\b"
    r"|\\bdonotreply\\b|\\bplease do not respond to this\\b"
    r"|\\bunattended\\b|\\bwithout (?:any )?human (?:intervention|review)\\b"
    r"|\\byou are receiving this (?:because|as)\\b"
    r"|\\bthis (?:is|was) (?:an? )?(?:automated|system|machine|auto)[\\s-]*(?:message|notification|email)?\\b)",
    re.IGNORECASE)


def strip_automation_wording(text: str) -> tuple[str, list[str]]:
    """Drop every sentence that presents the message as automated. Returns (clean, removed sentences)."""
    if not text:
        return text, []
    kept, removed = [], []
    for chunk in re.split(r"(?<=[.!?])\\s+|\\n", text):
        piece = chunk.strip()
        if not piece:
            continue
        if AUTOMATION_WORDING.search(piece):
            removed.append(piece)
            continue
        kept.append(piece)
    return " ".join(kept), removed


def strip_automation_subject(subject: str, fallback: str = "") -> tuple[str, list[str]]:
    """Same rule for a subject line, which has no sentences to drop."""
    clean, cut = strip_automation_wording(subject)
    if clean.strip():
        return clean.strip(), cut
    parts = [p.strip() for p in re.split(r"[:|\\u2014\\u2013]| - ", subject or "") if p.strip()]
    kept = [p for p in parts if not AUTOMATION_WORDING.search(p)]
    if kept:
        return " - ".join(kept), cut + ([subject] if subject.strip() else [])
    return (fallback or "").strip(), cut + ([subject] if subject.strip() else [])


def assert_human_sender(from_addr: str, from_name: str = "") -> None:
    """Refuse a sender that announces itself as machine-sent (no-reply@, automated@, a bot name)."""
    local = (from_addr or "").split("@")[0]
    if AUTOMATION_WORDING.search(local) or AUTOMATION_WORDING.search(from_name or ""):
        raise NotifyError(
            "refusing to send: the From address or display name reads as automated "
            f"({from_addr!r} / {from_name!r}). Use a plain human sender."
        )


'''
    if "def strip_automation_wording" in path.read_text(encoding="utf-8"):
        print("   notify.py guards: present")
        return
    text = path.read_text(encoding="utf-8")
    anchor = "CHANNELS = ("
    if anchor not in text:
        raise SystemExit("FAILED notify.py: no CHANNELS anchor")
    prefix = "" if "\nimport re\n" in text else "import re\n\n\n"
    path.write_text(text.replace(anchor, prefix + block + anchor, 1), encoding="utf-8")
    print("   notify.py guards: inserted")


ROUTE_SECTION = '''# ---------------------------------------------------------------- the employer-email route
# OWNER DECISIONS (21 Sep 2026): "add send mail to hr if application fails (manual apply and never say
# its applied by bot)", tightened to NO DOUBLE MAIL: one application, one follow-up, one reply per
# incoming message - and nothing else. The rule lives in this one command so it cannot drift between
# job prompts. See docs/APPLICATION_EMAIL.md.

APPLY_EMAIL_NAME = "apply_email.py"
ROUTE_ACTIONS = {"application": "emailed", "follow-up": "followed-up", "reply": "replied"}


def apply_email_module(d: pathlib.Path):
    """This candidate's apply_email.py: tools/ first (a deployment), then the engine checkout."""
    import importlib.util
    cands = [d / "tools" / APPLY_EMAIL_NAME, d / APPLY_EMAIL_NAME,
             pathlib.Path(__file__).resolve().parent / APPLY_EMAIL_NAME,
             pathlib.Path.home() / "jobhunt-agent" / "engine" / "notify" / APPLY_EMAIL_NAME]
    for cand in cands:
        if not cand.is_file():
            continue
        spec = importlib.util.spec_from_file_location("jha_apply_email", cand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise RuntimeError("apply_email.py was not found next to this tool or in the engine checkout")


def row_note(status: str, outcome_norm: str, date: str, route: str, evidence: str = "",
             note: str = "", apply_url: str = "") -> str:
    """The Notes string for one row write: `Applied <date>`, `Follow-up sent <date>`, or BROWSER NEEDED."""
    if status in ("Submitted", "Emailed"):
        head = (f"Follow-up sent {date}" if outcome_norm in ("follow-up", "followup")
                else f"Applied {date}")
        composed = head + (f" via {route}" if route else "")
    elif status == "Blocked":
        composed = f"BROWSER NEEDED: {apply_url or 'see row'}"
    else:
        composed = f"{status} {date}"
    for chunk in (evidence, note):
        if str(chunk).strip():
            composed += f" | {str(chunk).strip()}"
    return composed[:1200]


def route_application_email(d: pathlib.Path, pack, company: str, role: str, portal_url: str,
                            date: str, sender=None, kind: str = "application",
                            dry_run: bool = False, in_reply_to: str = "",
                            thread_id: str = "") -> dict:
    """The decision: emailed / followed-up / replied, or blocked (application) / unchanged."""
    if sender is None:
        sender = apply_email_module(d).run
    try:
        res = sender(pathlib.Path(pack).expanduser(), workspace=d, company=company, role=role,
                     portal_url=portal_url, kind=kind, dry_run=dry_run, in_reply_to=in_reply_to,
                     thread_id=thread_id)
    except Exception as exc:
        reason = str(exc)
        action = "blocked" if kind == "application" else "unchanged"
        return {"action": action, "reason": reason, "email": None, "kind": kind,
                "notes": (f"BROWSER NEEDED: {portal_url or 'see row'}" if action == "blocked" else ""),
                "evidence": f"application email refused: {reason}"}
    head = "application email" if kind == "application" else f"{kind} email"
    notes = {"application": f"Applied {date} via email (portal failed)",
             "follow-up": f"Follow-up sent {date} via email"}.get(kind, "")
    return {"action": ROUTE_ACTIONS.get(kind, "emailed"), "reason": "", "email": res, "kind": kind,
            "notes": notes,
            "evidence": (f"{head} to {res.get('to')} (source {res.get('to_source')})"
                         + (", CV + cover letter attached" if res.get("attachments") else "")
                         + (f"; portal failed: {portal_url}" if portal_url else ""))}


def cmd_apply_email(args) -> int:
    d = find_dir(args.dir)
    pack = pathlib.Path(args.pack).expanduser()
    if not pack.is_dir():
        print(f"no pack directory: {pack}", file=sys.stderr)
        return 2
    company, role = args.company or "", args.role or ""
    date = args.date or time.strftime("%Y-%m-%d")
    kind = args.kind or "application"
    decision = route_application_email(d, pack, company, role, args.portal_url, date, kind=kind,
                                       dry_run=args.dry_run, in_reply_to=args.in_reply_to,
                                       thread_id=args.thread_id)
    action = decision["action"]
    row = {"emailed": "Emailed", "followed-up": "Emailed", "blocked": "Blocked",
           "unchanged": "untouched"}[action]
    print(f"ROUTE: {action} -> row {row}   ({company or '?'} - {role or pack.name}) [{kind}]")
    res = decision["email"] or {}
    if action in ("emailed", "followed-up", "replied"):
        print(f"   to {res.get('to')} (source {res.get('to_source')})")
        print(f"   from {res.get('from_name')} <{res.get('from')}>")
        print(f"   subject: {res.get('subject')}")
        print(f"   attachments: {', '.join(res.get('attachments') or []) or 'none'}")
        if res.get("in_reply_to"):
            print(f"   in-reply-to {res.get('in_reply_to')} (thread {res.get('thread_id') or 'n/a'})")
        if res.get("sanitised"):
            print(f"   automation wording removed from {len(res['sanitised'])} line(s)")
        if res.get("dry_run"):
            print("   dry run: nothing sent, no ledger entry")
    else:
        print(f"   reason: {decision['reason']}")
        if decision.get("notes"):
            print(f"   row note: {decision['notes']}")
    if args.dry_run:
        print("   dry run: no tracker row written")
        return 0
    if action in ("unchanged", "replied"):
        print("   row untouched (no tracker status change for this kind)")
        return 0

    location, fit = "", 0
    _, rows = parse_rows(d / "build_tracker.py")
    row_obj, _reason = find_row(rows, company, role) if (company and role) else (None, "not in tracker")
    if row_obj is not None:
        location, fit = str(row_obj[3]), row_obj[4]
    attachments = ",".join(res.get("attachments") or []) if action == "emailed" else ""
    outcome = {"emailed": "emailed", "followed-up": "follow-up", "blocked": "blocked"}[action]
    route = {"emailed": "email (portal failed)", "followed-up": "email", "blocked": ""}[action]
    tsv = d / "data" / f"apply-email-route-{time.time_ns()}.tsv"
    tsv.parent.mkdir(exist_ok=True)
    cells = [pack.name, outcome, decision["evidence"], "", attachments, str(pack / "jd.md"),
             args.portal_url, route, date + "T00:00:00Z", company, role, location, str(fit)]
    tsv.write_text("\\t".join(cells) + "\\n", encoding="utf-8")
    try:
        rc = cmd_apply_results(argparse.Namespace(dir=str(d), results=str(tsv), roles=None))
    finally:
        tsv.unlink(missing_ok=True)
    return 0 if rc in (0, 5) else rc


'''


def deploy_jt_py(tools: pathlib.Path) -> None:
    path = tools / "jt.py"
    text = path.read_text(encoding="utf-8")
    if "apply-email" in text:
        print("   jt.py gate: present")
        return
    edits = [
        ('''  python3 tools/jt.py apply-results --results <tsv> [--roles <roles.json>] [--dir <folder>]
  python3 tools/jt.py sync''',
         '''  python3 tools/jt.py apply-results --results <tsv> [--roles <roles.json>] [--dir <folder>]
  python3 tools/jt.py apply-email --pack <applications/<slug>> [--kind application|follow-up|reply]
  python3 tools/jt.py sync'''),
        ('''    "offer": "Offer", "rejected": "Rejected",
}''',
         '''    "offer": "Offer", "rejected": "Rejected",
    # a follow-up is still a message to that employer about the same role: the row stays Emailed
    "follow-up": "Emailed", "followup": "Emailed",
}'''),
        ('''        if status == "Submitted" or status == "Emailed":
            composed = f"Applied {date}" + (f" via {route}" if route else "")
        elif status == "Blocked":
            composed = f"BROWSER NEEDED: {apply_url or 'see row'}"
        else:
            composed = f"{status} {date}"
        for chunk in (evidence, note):
            if chunk.strip():
                composed += f" | {chunk.strip()}"
        composed = composed[:1200]''',
         '''        composed = row_note(status, outcome_norm, date, route, evidence, note, apply_url)'''),
        ('''def cmd_apply_results(args) -> int:''',
         ROUTE_SECTION.replace('def row_note(', 'def row_note(').replace(
             'def route_application_email', 'def route_application_email') +
         '''def cmd_apply_results(args) -> int:'''),
        ('''    p = sub.add_parser("sync", help="push this candidate's Google Sheet now")''',
         '''    p = sub.add_parser("apply-email", help="route a failed/walled portal application by email")
    p.add_argument("--dir", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    p.add_argument("--pack", required=True, help="the role pack (applications/<slug>)")
    p.add_argument("--company")
    p.add_argument("--role")
    p.add_argument("--portal-url", default="", help="the portal URL that failed (goes in the row)")
    p.add_argument("--date", default="", help="application date for the Notes (default: today)")
    p.add_argument("--kind", default="application",
                   help="application | follow-up | reply (nothing else; no double mail)")
    p.add_argument("--in-reply-to", default="",
                   help="the incoming Gmail message id a reply answers (required for --kind reply)")
    p.add_argument("--thread-id", default="", help="Gmail threadId for a reply, if known")
    p.add_argument("--dry-run", action="store_true", help="decide and print; send nothing, write no row")
    p.set_defaults(func=cmd_apply_email)

    p = sub.add_parser("sync", help="push this candidate's Google Sheet now")'''),
    ]
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit(f"FAILED jt.py anchor ({text.count(old)}x): {old.splitlines()[0][:70]}")
        text = text.replace(old, new, 1)
    # row_note and the route section must not both define row_note twice: the route section has it once
    path.write_text(text, encoding="utf-8")
    import ast
    ast.parse(text)
    print("   jt.py gate: inserted")


def deploy_config(ws: pathlib.Path, slug: str) -> None:
    path = ws / "notify.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if "application_email" in data:
        print("   notify.json block: present")
        return
    data["application_email"] = {
        "_comment": ("Employer mail, allowed ONLY when a portal application failed or was impossible. "
                     "No double mail: one application, one follow-up (after the wait), one reply per "
                     "incoming message, and nothing else. The mail is sent as the candidate and never "
                     "mentions automation."),
        "enabled": bool(ENABLED.get(slug, False)),
        "from_name": FROM_NAME.get(slug, ""),
        "signature": "",
        "max_per_run": 1,
        "require_attachments": True,
        "followup_after_business_days": 7,
        "availability": AVAILABILITY.get(slug, ""),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"   notify.json block: inserted (enabled={data['application_email']['enabled']})")


def main() -> int:
    for slug, ws in sorted((p.name, p / "workspace") for p in PROFILES.iterdir()
                           if (p / "workspace").is_dir()):
        tools = ws / "tools"
        if not tools.is_dir():
            print(f"{slug}: no tools/ - skipped")
            continue
        print(f"{slug}: {ws}")
        if slug in ENABLED:
            shutil.copy2(REPO / "engine" / "notify" / "apply_email.py", tools / "apply_email.py")
            print("   apply_email.py: copied")
            deploy_notify_py(tools)
            deploy_jt_py(tools)
        deploy_config(ws, slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
