#!/usr/bin/env python3
"""Repair tests/test_prompt_playbook.py after a broken heredoc left a truncated class at the end."""
import pathlib
import shutil
import time

P = pathlib.Path("/home/ubuntu/jobhunt-agent/tests/test_prompt_playbook.py")
text = P.read_text(encoding="utf-8")
cut = text.index('class TestTheDashRuleIsNotALostRule')
head = text[:cut].rstrip() + "\n"
assert head.rstrip().endswith('unittest.main()') or 'unittest.main()' in head, "unexpected head shape"

BLOCK = '''

class TestTheDashRuleIsNotALostRule(unittest.TestCase):
    """The repo forbids the em/en dash glyph in tracked files, so a rule that NAMES the character has to
    spell it as a code point. That reword must not read as a rule the prompt shed.
    """

    def test_a_dash_only_rewording_is_not_reported_as_loss(self):
        original = "NEVER use the em-dash character (\\u2014) in ANY material."
        reachable = "NEVER use the em-dash (U+2014) or en-dash (U+2013) in ANY material."
        self.assertEqual(pp.missing_lines(original, reachable), [])

    def test_a_genuinely_deleted_line_is_still_reported(self):
        self.assertEqual(pp.missing_lines("- alpha\\n- beta\\n", "- alpha\\n"), ["- beta"])

    def test_the_playbook_folds_both_dash_characters(self):
        self.assertEqual(pp.fold_dashes("a \\u2014 b \\u2013 c"), "a - b - c")
'''
shutil.copy2(P, P.with_name(P.name + ".bak-repair-" + time.strftime("%Y%m%d-%H%M%S")))
P.write_text(head + BLOCK, encoding="utf-8")
import ast
ast.parse(P.read_text(encoding="utf-8"))
print("repaired:", len(P.read_text(encoding='utf-8').splitlines()), "lines, parses OK")
