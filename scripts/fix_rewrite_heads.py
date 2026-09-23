#!/usr/bin/env python3
"""Teach the lossless check about the two lines the repo's own dash ban forced us to reword.

The check exists to catch a rule that VANISHED. Two lines were reworded, not dropped: the strict-format
rule had to stop printing the dash glyph (tests/test_ship_clean.py bans it in tracked files), and the
years-of-experience line carried the same glyph. A line whose HEAD is on this list counts as reachable when
the other side still carries a line with that head.
"""
import pathlib
import shutil
import time

P = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/tools/prompt_playbook.py")
BLOCK = '''

# Lines the repo's own dash ban forced us to reword (the glyph is banned in tracked files, so a rule that
# NAMES the character has to spell it as a code point). These heads count as reachable when the other side
# still carries a line with the same head: the rule is still there, its wording moved with the ban.
REWORDED_HEADS = (
    "NEVER use the em-dash",
    "Do NOT reject a role solely for years-of-experience requirements",
)


def _head_satisfied(gone: str, reachable_lines: list) -> bool:
    """Is this reworded line still represented by a line with the same head?"""
    for head in REWORDED_HEADS:
        if gone.lstrip().startswith(head) or head in gone:
            return any(head in ln for ln in reachable_lines)
    return False
'''

text = P.read_text(encoding="utf-8")
if "REWORDED_HEADS" in text:
    print("heads already present")
else:
    anchor = "def missing_lines(original: str, reachable: str) -> list:"
    assert text.count(anchor) == 1
    text = text.replace(anchor, BLOCK.strip() + "\n\n\n" + anchor, 1)
    old_tail = """        else:
            gone.append(ln)
    return gone"""
    new_tail = """        else:
            gone.append(ln)
    if gone and REWORDED_HEADS:
        lines = body_lines(reachable)
        gone = [ln for ln in gone if not _head_satisfied(ln, lines)]
    return gone"""
    assert text.count(old_tail) == 1, "tail anchor not unique"
    text = text.replace(old_tail, new_tail)
    shutil.copy2(P, P.with_name(P.name + ".bak-rewriteheads-" + time.strftime("%Y%m%d-%H%M%S")))
    P.write_text(text, encoding="utf-8")
    import ast
    ast.parse(text)
    print("prompt_playbook.py: rewrite-head awareness added and parses")
