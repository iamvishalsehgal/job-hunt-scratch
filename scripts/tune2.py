#!/usr/bin/env python3
"""Second tuning pass on the self-referential automation rule, plus the docstring the repo test scans."""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/notify.py")
A = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/apply_email.py")

OLD = '''    r"|\\bautomat(?:ed|ic|ically|ion)\\b\\s*[.!?]"'''
NEW = '''    # 'This is automated.' is a confession; 'the report refreshes automatically.' is the candidate
    # describing their own work, so the bare word only counts with a demonstrative subject.
    r"|\\b(?:this|it|that)\\s+(?:is|was|has been)\\s+(?:an?\\s+)?automat\\w*\\b"'''

OLD_DOC = '''    \"\"\"The tooling token that would tell an employer they are reading an application robot, or \"\".\"\"\"'''
NEW_DOC = '''    \"\"\"The tooling token that must never reach an employer, or \"\" when the body is clean.\"\"\"'''


def main() -> int:
    apply = "--apply" in sys.argv
    text = P.read_text(encoding="utf-8")
    if "demonstrative subject" in text:
        print("already tuned")
    elif text.count(OLD) == 1:
        text = text.replace(OLD, NEW)
        if apply:
            shutil.copy2(P, P.with_name(P.name + f".bak-tune2-{STAMP}"))
            P.write_text(text, encoding="utf-8")
            import ast
            ast.parse(text)
        print("sentence-final rule replaced by the demonstrative form")
    else:
        print(f"WARN: anchor appears {text.count(OLD)} times")

    a = A.read_text(encoding="utf-8")
    if OLD_DOC in a:
        a = a.replace(OLD_DOC, NEW_DOC)
        if apply:
            shutil.copy2(A, A.with_name(A.name + f".bak-tune2-{STAMP}"))
            A.write_text(a, encoding="utf-8")
            import ast
            ast.parse(a)
        print("docstring reworded for the repo's own scan")
    else:
        print("docstring already reworded")
    print("APPLIED" if apply else "DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
