#!/usr/bin/env python3
"""Append the dash-fold tests to tests/test_prompt_playbook.py (idempotent)."""
import pathlib

P = pathlib.Path("/home/ubuntu/jobhunt-agent/tests/test_prompt_playbook.py")
MARK = "class TestTheDashRuleIsNotALostRule"
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

text = P.read_text(encoding="utf-8")
if MARK in text:
    print("already present")
else:
    P.write_text(text.rstrip() + "\n" + BLOCK, encoding="utf-8")
    print("appended dash-fold tests:", len(P.read_text(encoding='utf-8')), "chars")
