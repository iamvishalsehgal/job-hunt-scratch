#!/usr/bin/env python3
"""Make the no-automation rule self-referential, so it stops deleting real professional sentences.

Found while testing the bot-wording rule: `\\bautomated\\b`, `\\bautomation\\b`, `\\bautomatic\\b` and
`\\bautomatically\\b` matched ANY use, so a legitimate application sentence such as 'I automated the nightly
reconciliation and the report refreshes automatically' was deleted from the body - the rule exists to stop the
EMAIL describing ITSELF as automated, not to police the candidate's vocabulary about their own work.

The four bare words are replaced by one proximity rule: an automation word counts only when a
self-referential noun (message, email, reply, notification, notice, response, system) appears within a few
words of it. The explicit 'automated message/email/...' shapes stay as they were, so nothing that used to be
caught for the right reason is lost.

Usage: precise_automation.py [--apply]
"""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/notify.py")

OLD = '''    r"(?:\\bautomated\\b|\\bautomatic\\b|\\bautomatically\\b|\\bautomation\\b|\\bautomat(?:ed|ic) (?:message|email|notification|alert|system|reply)\\b"'''
NEW = '''    r"(?:\\bautomat(?:ed|ic) (?:message|email|notification|alert|system|reply)\\b"
    r"|\\bautomat(?:ed|ic|ically|ion)\\b(?=\\W+(?:\\w+\\W+){0,3}?(?:message|email|e-mail|reply|notification|notice|response|system)\\b)"'''


def main() -> int:
    apply = "--apply" in sys.argv
    text = P.read_text(encoding="utf-8")
    if "automat(?:ed|ic|ically|ion)" in text:
        print("already precise")
        return 0
    if text.count(OLD) != 1:
        print(f"REFUSED: anchor appears {text.count(OLD)} times")
        return 1
    text = text.replace(OLD, NEW)
    print("automation rule made self-referential")
    if apply:
        shutil.copy2(P, P.with_name(P.name + f".bak-preciseauto-{STAMP}"))
        P.write_text(text, encoding="utf-8")
        import ast
        ast.parse(text)
        print("written and parses")
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
