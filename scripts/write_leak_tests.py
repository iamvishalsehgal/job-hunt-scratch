import pathlib
P = pathlib.Path("/home/ubuntu/jobhunt-agent/tests/test_email_no_machinery.py")
P.write_text('''"""No employer may ever see the workspace's own working notes or the pipeline's machinery.

Measured 23 Sep 2026: a SENT application email carried the line `Recipient evidence: ... email_guard exit 20
SEND_GENERIC (department mailbox, valid).` and a draft opened with a markdown heading naming the pack. The
parser only dropped the meta lines it knew, so both travelled with the application.
"""
from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

TENNET = (
    "# email to HR - TenneT TSO B.V., Data Engineer Market Analysis (Arnhem)\\n"
    "\\n"
    "To: miguel.ortiz@tennet.eu (Miguel Ortiz, Recruiter, named in the posting, job 117284)\\n"
    "Cc: sollicitatie@tennet.eu (application mailbox named in the posting)\\n"
    "Subject: Application - Data Engineer Market Analysis - Jane Doe\\n"
    "\\n"
    "Dear Miguel,\\n"
    "\\n"
    "I would like to apply for the role.\\n"
)

MOMO = (
    "To: career@momomedical.com\\n"
    "Recipient evidence: momomedical.com/contact, section \\"Vacancies\\". email_guard exit 20 SEND_GENERIC.\\n"
    "Subject: Application: Backend Developer - Jane Doe\\n"
    "\\n"
    "Dear Momo Medical hiring team,\\n"
    "\\n"
    "I am applying for the role.\\n"
)


def load():
    spec = importlib.util.spec_from_file_location("jha_leak", ROOT / "engine" / "notify" / "apply_email.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAnnotationsNeverTravel(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def _write(self, body):
        p = pathlib.Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        f = p / "email-to-hr.md"
        f.write_text(body, encoding="utf-8")
        return self.m.parse_draft(f)

    def test_a_markdown_heading_is_dropped(self):
        subject, body, dropped = self._write(TENNET)
        self.assertNotIn("#", body)
        self.assertNotIn("email to HR", body)
        self.assertEqual(subject, "Application - Data Engineer Market Analysis - Jane Doe")
        self.assertTrue(body.startswith("Dear Miguel,"))

    def test_a_recipient_evidence_line_is_dropped(self):
        subject, body, dropped = self._write(MOMO)
        self.assertNotIn("Recipient evidence", body)
        self.assertNotIn("email_guard", body)
        self.assertNotIn("SEND_GENERIC", body)
        self.assertTrue(body.startswith("Dear Momo Medical hiring team,"))

    def test_the_recipient_is_still_discovered_from_the_same_draft(self):
        """Widening what is STRIPPED must not change which address mail goes to."""
        self.assertIn(self.m.DRAFT_PRIMARY.match("To: career@momomedical.com"), "match")
        self.assertIsNotNone(self.m.DRAFT_PRIMARY.match("To: career@momomedical.com"))

    def test_a_body_with_prose_only_is_untouched(self):
        good = "Dear team,\\n\\nI am applying for the role.\\n\\nKind regards,\\nJane\\n"
        clean, dropped = self.m.strip_internal_notes(good)
        self.assertEqual(clean, good.rstrip("\\n"))
        self.assertEqual(dropped, [])

    def test_a_line_that_starts_with_a_meta_word_is_dropped(self):
        clean, dropped = self.m.strip_internal_notes("Dear team,\\n\\nNote: pack built by the sweep.\\n")
        self.assertEqual(dropped, ["Note: pack built by the sweep."])
        self.assertNotIn("sweep", clean)

    def test_a_salary_line_is_content_and_survives(self):
        body = "Dear team,\\n\\nSalary expectation: EUR 4,400 to 5,000 gross per month base.\\n"
        clean, dropped = self.m.strip_internal_notes(body)
        self.assertIn("Salary expectation", clean)
        self.assertEqual(dropped, [])


class TestTheMachineryIsRefused(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_a_leaked_token_is_a_refusal(self):
        for token in ("email_guard", "SEND_GENERIC", "exit 20", "jt.py", "build_tracker", "the tracker",
                      "row_gate", "playbook", "applications/"):
            with self.subTest(token=token):
                self.assertTrue(self.m.internal_leak_problem(f"Dear team,\\n\\nI ran {token} today.\\n"))

    def test_an_ordinary_application_body_is_clean(self):
        body = ("Dear team,\\n\\nI own the SQL Server warehouse and audited 704 ETL processes.\\n\\n"
                "My data quality gates caught 12 upstream breaks last quarter.\\n")
        self.assertEqual(self.m.internal_leak_problem(body), "")

    def test_the_layer_composes_with_the_scrub(self):
        body = "Dear team,\\n\\nRecipient evidence: email_guard exit 20.\\n\\nI am applying.\\n"
        clean, dropped = self.m.strip_internal_notes(body)
        self.assertEqual(self.m.internal_leak_problem(clean), "", "the annotation line was stripped first")


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
import ast
ast.parse(P.read_text())
print("written", len(P.read_text()), "chars, parses OK")
