#!/usr/bin/env python3
"""Owner rule 23 Sep 2026: never let an employer learn they are talking to a bot.

AUTOMATION_WORDING already catches 'automated', 'do not reply', 'robot' and friends. What it did not catch is
the assistant vocabulary an agent reaches for when it explains itself: 'as an AI', 'language model', 'the
job-hunt bot', 'this tool sent'. Those sentences are added here.

Deliberately NOT added: 'AI', 'pipeline', 'automation' and 'algorithm' on their own. In this candidate's
domain those are ordinary professional words (an 'AI/ML' project, a 'data pipeline', 'automation of ETL'), and
banning them would strip real content from a real application.

Usage: extend_bot_wording.py [--apply]
"""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/notify.py")

OLD_TAIL = '''    r"|\\byou are receiving this (?:because|as)\\b"
    r"|\\bthis (?:is|was) (?:an? )?(?:automated|system|machine|auto)[\\s-]*(?:message|notification|email)?\\b)",
    re.IGNORECASE)'''

NEW_TAIL = '''    r"|\\byou are receiving this (?:because|as)\\b"
    r"|\\bthis (?:is|was) (?:an? )?(?:automated|system|machine|auto)[\\s-]*(?:message|notification|email)?\\b"
    # Owner rule 23 Sep 2026: an employer must never learn they are talking to a bot. These are the shapes an
    # agent reaches for when it explains itself. Bare 'AI', 'pipeline', 'automation' and 'algorithm' stay out:
    # in this domain they are ordinary professional words and banning them would strip real content.
    r"|\\bas an ai\\b|\\bai assistant\\b|\\b(?:large )?language model\\b|\\bllm\\b|\\bai model\\b"
    r"|\\b(?:an? )?artificial intelligence (?:assistant|system)\\b"
    r"|\\bthe (?:job[- ]?hunt|application) (?:bot|agent|assistant|tool|engine|system|pipeline)\\b"
    r"|\\b(?:this|our|my) (?:bot|assistant|agent|tool|engine) (?:sent|wrote|generated|checked|ran)\\b"
    r"|\\bwritten by (?:an? )?(?:ai|bot|tool|program|machine|model)\\b"
    r"|\\bautomated (?:assistant|agent|bot)\\b)",
    re.IGNORECASE)'''


def main() -> int:
    apply = "--apply" in sys.argv
    text = P.read_text(encoding="utf-8")
    if "language model" in text:
        print("already extended")
        return 0
    if text.count(OLD_TAIL) != 1:
        print(f"REFUSED: anchor appears {text.count(OLD_TAIL)} times")
        return 1
    text = text.replace(OLD_TAIL, NEW_TAIL)
    print("AUTOMATION_WORDING extended")
    if apply:
        shutil.copy2(P, P.with_name(P.name + f".bak-botwording-{STAMP}"))
        P.write_text(text, encoding="utf-8")
        import ast
        ast.parse(text)
        print("written and parses")
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
