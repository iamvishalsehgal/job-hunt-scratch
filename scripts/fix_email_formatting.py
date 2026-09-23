#!/usr/bin/env python3
"""Owner rule 23 Sep 2026: format the email; never one paragraph.

Root cause found in the code, not the prompt: every outgoing employer message passes through
notify.strip_automation_wording(), which split the text on sentence ends AND newlines and then rejoined the
pieces with a single space. An email written as greeting / body paragraphs / sign-off therefore reached the
employer as ONE run-on paragraph.

The scrub still has to drop sentences that present the message as automated (that rule is unchanged), but it
must do it per LINE and keep the line and blank-line structure. Sentence-level removal inside a line stays
exactly as it was.

Usage: fix_email_formatting.py [--apply]
"""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/notify.py")

OLD = '''def strip_automation_wording(text: str) -> tuple[str, list[str]]:
    """Drop every sentence that presents the message as automated. Returns (clean, removed sentences).

    Sentence-level on purpose: rewriting inside a sentence leaves fragments, and a fragment is worse
    than a missing line. Callers record what was removed so the edit is auditable.
    """
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
'''

NEW = '''def strip_automation_wording(text: str) -> tuple[str, list[str]]:
    """Drop every sentence that presents the message as automated. Returns (clean, removed sentences).

    Sentence-level on purpose: rewriting inside a sentence leaves fragments, and a fragment is worse
    than a missing line. Callers record what was removed so the edit is auditable.

    THE PARAGRAPH STRUCTURE IS PART OF THE MESSAGE. This used to split on sentence ends and newlines and
    rejoin everything with a single space, so every employer email arrived as one run-on paragraph - a
    formatted draft with a greeting, three paragraphs and a sign-off collapsed into a blob (measured
    23 Sep 2026). The scrub now works line by line and preserves the blank line between paragraphs; only
    the sentences inside a line are re-spaced. A line that is entirely automation wording disappears with
    the paragraph break it left behind, so nothing double-spaces.
    """
    if not text:
        return text, []
    kept_lines, removed = [], []
    for line in str(text).split("\\n"):
        if not line.strip():
            kept_lines.append("")
            continue
        keep = []
        for piece in re.split(r"(?<=[.!?])\\s+", line):
            bit = piece.strip()
            if not bit:
                continue
            if AUTOMATION_WORDING.search(bit):
                removed.append(bit)
                continue
            keep.append(bit)
        kept_lines.append(" ".join(keep))
    # One blank line between paragraphs, none at the edges: dropping a whole line must not leave a gap.
    out = []
    for line in kept_lines:
        if not line.strip() and (not out or not out[-1].strip()):
            continue
        out.append(line.rstrip())
    while out and not out[-1].strip():
        out.pop()
    return "\\n".join(out), removed
'''


def main() -> int:
    apply = "--apply" in sys.argv
    text = P.read_text(encoding="utf-8")
    if "THE PARAGRAPH STRUCTURE IS PART OF THE MESSAGE" in text:
        print("already patched")
        return 0
    if text.count(OLD) != 1:
        print(f"REFUSED: anchor appears {text.count(OLD)} times")
        return 1
    text = text.replace(OLD, NEW)
    print(f"notify.py: {len(P.read_text(encoding='utf-8'))} -> {len(text)} chars")
    if apply:
        shutil.copy2(P, P.with_name(P.name + f".bak-paragraphs-{STAMP}"))
        P.write_text(text, encoding="utf-8")
        import ast
        ast.parse(text)
        print("written and parses")
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
