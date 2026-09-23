import pathlib
P = pathlib.Path("/home/ubuntu/jobhunt-agent/tests/test_email_paragraphs.py")
BODY = '''"""The paragraphs an email is written with must survive the automation-wording scrub.

Measured 23 Sep 2026: the scrub split on sentence ends AND newlines and rejoined with a single space, so a
formatted application email (greeting, three paragraphs, sign-off) arrived as one run-on paragraph. These
tests pin the structure, and pin that the scrub still drops what it is for.
"""
from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

FORMATTED = (
    "Dear Acme recruiting team,\\n"
    "\\n"
    "I am applying for the Data Engineer role in Amsterdam. My CV and cover letter are attached.\\n"
    "\\n"
    "At Van den Bosch I own the SQL Server warehouse and audited 704 ETL processes.\\n"
    "\\n"
    "Kind regards,\\n"
    "Jane Doe | jane@example.com | +31 6 00000000\\n"
)


def load_notify():
    spec = importlib.util.spec_from_file_location("jha_notify_paras", ROOT / "engine" / "notify" / "notify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTheParagraphsSurvive(unittest.TestCase):
    def setUp(self):
        self.n = load_notify()

    def test_a_formatted_body_keeps_its_blank_lines(self):
        clean, removed = self.n.strip_automation_wording(FORMATTED)
        self.assertEqual(removed, [])
        self.assertEqual(clean, FORMATTED.rstrip("\\n"), "the paragraph breaks were collapsed")
        self.assertGreaterEqual(clean.count("\\n\\n"), 3)

    def test_it_is_never_one_paragraph(self):
        clean, _ = self.n.strip_automation_wording(FORMATTED)
        self.assertGreater(len([ln for ln in clean.splitlines() if ln.strip()]), 3)
        self.assertIn("\\n\\n", clean)

    def test_a_dropped_sentence_does_not_collapse_the_rest(self):
        body = ("Dear team,\\n\\n"
                "This is an automated message from the job hunt system.\\n\\n"
                "I am applying for the role.\\n\\nKind regards,\\nJane Doe\\n")
        clean, removed = self.n.strip_automation_wording(body)
        self.assertEqual(len(removed), 1)
        self.assertIn("Dear team,", clean)
        self.assertIn("I am applying for the role.", clean)
        self.assertIn("\\n\\n", clean, "the paragraphs are still paragraphs")
        self.assertNotIn("\\n\\n\\n", clean, "the dropped line must not leave a double gap")

    def test_a_whole_paragraph_of_automation_goes_without_a_gap(self):
        body = "Dear team,\\n\\nAutomated. Do not reply.\\n\\nRegards,\\nJane\\n"
        clean, removed = self.n.strip_automation_wording(body)
        self.assertEqual(len(removed), 2)
        self.assertNotIn("\\n\\n\\n", clean)
        self.assertTrue(clean.startswith("Dear team,"))

    def test_a_one_line_subject_is_unaffected(self):
        clean, removed = self.n.strip_automation_wording("Application - Data Engineer - Jane Doe")
        self.assertEqual(clean, "Application - Data Engineer - Jane Doe")
        self.assertEqual(removed, [])

    def test_an_automation_subject_still_empties(self):
        clean, removed = self.n.strip_automation_wording("Automated alert: Acme - interview")
        self.assertEqual(clean, "")
        self.assertEqual(len(removed), 1)

    def test_empty_input_is_still_empty(self):
        self.assertEqual(self.n.strip_automation_wording(""), ("", []))


if __name__ == "__main__":
    unittest.main()
'''
P.write_text(BODY, encoding="utf-8")
import ast
ast.parse(BODY)
print("written", len(BODY), "chars, parses OK")
