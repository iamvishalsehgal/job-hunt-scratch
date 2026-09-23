#!/usr/bin/env python3
"""Stop the workspace's own working notes from reaching an employer.

Measured 23 Sep 2026: a SENT application email (Momo Medical, ledger ok=True) carried the line
    Recipient evidence: momomedical.com/contact ... email_guard exit 20 SEND_GENERIC (department mailbox, valid).
and a draft opened with
    # email to HR - TenneT TSO B.V., Data Engineer Market Analysis (Arnhem)
The parser only dropped the `To:` / `Cc:` / `Wants:` lines it knew about, so a markdown heading and an
annotation line travelled with the application. An employer must never see the machinery.

Design: recipient DISCOVERY keeps its own known-good matcher (DRAFT_META) untouched, because that code path
decides which address an application goes to. A separate, wider ANNOTATION_RE governs what is STRIPPED from
the body, so widening the net cannot change where mail is sent.

Three layers:
1. `ANNOTATION_RE` - headings (#), evidence/source/route/portal/guard/exit/kind/status/notes annotations.
   Whole lines are dropped, never rewritten: a fragment is worse than a missing line. `salary:` is
   deliberately absent - a salary line is legitimate content.
2. `strip_internal_notes()` - the same rule applied to a body assembled any other way, folding a blank line
   left behind so the message does not inherit a gap.
3. `internal_leak_problem()` - REFUSES the send when a tooling token survives inside prose, because a token
   in a sentence means something was pasted into the body, not merely mis-marked.

Usage: fix_internal_leak.py [--apply]
"""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/apply_email.py")

OLD_PARSE = '''        if DRAFT_META.match(stripped):
            dropped.append(stripped)
            continue'''
NEW_PARSE = '''        if DRAFT_META.match(stripped) or ANNOTATION_RE.match(stripped):
            dropped.append(stripped)
            continue'''

ANCHOR_META = '''DRAFT_WANTS = re.compile(r"^(?:wants?|asks)\\s*:\\s*(.+)$", re.I)'''
ADD_ANNOTATION = '''# What the workspace writes FOR ITSELF. Wider than DRAFT_META on purpose: DRAFT_META decides which address
# a send goes to, so it stays exactly as it was; this one only decides what is stripped out of the body.
# A line starting with `#` is a markdown heading a pack wrote for its own readers, never a sentence an
# employer should receive. `salary` is NOT here: a salary line is legitimate content.
ANNOTATION_RE = re.compile(
    r"^\\s*#{1,6}\\s+\\S"
    r"|^(?:recipient evidence|evidence|source|why|route|portal|guard|email_guard|exit|kind|status|ats"
    r"|note|notes|internal|draft|meta)\\s*:",
    re.I)

''' + ANCHOR_META

OLD_CALLER = '''        body, signed = ensure_signature(body, identity)'''
NEW_CALLER = '''        body, signed = ensure_signature(body, identity)
        # The workspace's own annotations never travel, whichever path assembled the body.
        body, dropped_now = strip_internal_notes(body)
        dropped += dropped_now'''

OLD_TAIL = '''    if problems:
        raise ApplyEmailError("refusing to send: " + "; ".join(problems))'''
NEW_TAIL = '''    leak = internal_leak_problem(body)
    if leak:
        problems.append(leak)
    if problems:
        raise ApplyEmailError("refusing to send: " + "; ".join(problems))'''

HELPERS = '''

def strip_internal_notes(body: str) -> tuple:
    """Drop the workspace's own annotation lines. Returns (clean, dropped lines)."""
    kept, dropped = [], []
    for line in str(body or "").splitlines():
        if line.strip() and ANNOTATION_RE.match(line.strip()):
            dropped.append(line.strip())
            continue
        kept.append(line)
    out = []
    for line in kept:
        if not line.strip() and (not out or not out[-1].strip()):
            continue
        out.append(line.rstrip())
    while out and not out[-1].strip():
        out.pop()
    return "\\n".join(out), dropped


# Tooling vocabulary that must never reach an employer (owner rule, 23 Sep 2026): an application email that
# names the guard, the tracker or the engine tells the reader they are talking to a machine.
INTERNAL_LEAK_RE = re.compile(
    r"(?:\\bemail[_-]?guard\\b|\\bSEND_[A-Z]+\\b|\\bexit (?:code )?\\d{1,3}\\b|\\bapply_email\\b|\\bjt\\.py\\b"
    r"|\\bbuild_tracker\\b|\\bgrade_?gate\\b|\\brow_gate\\b|\\bping_gate\\b|\\bdutch_gate\\b|\\bplaybook\\b"
    r"|\\btracker\\b|\\bledger\\b|\\bcron\\b|\\bworkspace\\b|\\bapplications/\\b|\\bexecutions\\.db\\b)",
    re.I)


def internal_leak_problem(body: str) -> str:
    """The tooling token that would tell an employer they are reading an application robot, or ""."""
    found = INTERNAL_LEAK_RE.search(str(body or ""))
    if not found:
        return ""
    return (f"the body mentions the pipeline's own machinery ({found.group(0)!r}), which an employer must "
            f"never see: remove that line and send again")
'''


def main() -> int:
    apply = "--apply" in sys.argv
    text = P.read_text(encoding="utf-8")
    if "ANNOTATION_RE" in text:
        print("already patched")
        return 0
    if "ANNOTATION_RE" in text:
        pass
    edits = [(OLD_PARSE, NEW_PARSE, "parse_draft drops annotations too"),
             (ANCHOR_META, ADD_ANNOTATION, "ANNOTATION_RE defined"),
             (OLD_CALLER, NEW_CALLER, "draft body stripped"),
             (OLD_TAIL, NEW_TAIL, "refusal wired")]
    for old, new, label in edits:
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: {label} anchor appears {n} times")
            return 1
        text = text.replace(old, new)
        print(f"  ok  {label}")
    anchor = "def parse_draft(path):"
    text = text.replace(anchor, HELPERS.strip() + "\n\n\n" + anchor, 1)
    print("  ok  helpers added")
    if apply:
        shutil.copy2(P, P.with_name(P.name + f".bak-internalleak-{STAMP}"))
        P.write_text(text, encoding="utf-8")
        import ast
        ast.parse(text)
        print("written and parses")
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
