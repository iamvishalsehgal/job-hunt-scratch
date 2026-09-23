import pathlib
P = pathlib.Path("/home/ubuntu/jobhunt-agent/tests/test_offpeak_schedule.py")
P.write_text('''"""Every model-using job runs only in DeepSeek's off-peak window.

Owner rule, 23 Sep 2026: the sweeps and the mail job must not run while DeepSeek charges peak rates. Official
pricing: peak is 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday; every other hour is off-peak (half price).

Script-only jobs (no_agent) cost no model tokens and are deliberately out of scope: the tracker/sheet sync and
the publish job keep their cadence.
"""
from __future__ import annotations

import json
import pathlib
import unittest

PROFILES = pathlib.Path.home() / ".hermes" / "profiles"
PEAK_HOURS = {1, 2, 3, 6, 7, 8, 9}
GOVERNED = ("-job-hunt", "-mail")


def live_jobs():
    for store in sorted(PROFILES.glob("*/cron/jobs.json")):
        data = json.loads(store.read_text(encoding="utf-8")) or {}
        for job in data.get("jobs", []):
            yield store.parent.name, job


def hours_in(expr: str):
    """The hour field of a 5-field cron expression, expanded."""
    fields = str(expr or "").split()
    if len(fields) != 5:
        return None
    out = set()
    for part in fields[1].split(","):
        if part == "*" or part.startswith("*/"):
            return set(range(24))
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


class TestTheSweepsAvoidPeakHours(unittest.TestCase):
    def setUp(self):
        self.jobs = [(slug, j) for slug, j in live_jobs()
                     if str(j.get("name", "")).endswith(GOVERNED)]

    def test_the_live_jobs_were_found(self):
        if not self.jobs:
            self.skipTest("no live profile store on this host")

    def test_no_governed_job_can_fire_in_a_peak_hour(self):
        for slug, job in self.jobs:
            sched = job.get("schedule") or {}
            expr = sched.get("expr") if isinstance(sched, dict) else str(sched or "")
            with self.subTest(job=job["name"]):
                hours = hours_in(expr)
                self.assertIsNotNone(hours, "an interval schedule cannot express an off-peak window")
                self.assertEqual(sorted(hours.intersection(PEAK_HOURS)), [],
                                 f"{job['name']} fires in peak hour(s)")

    def test_the_window_is_all_the_other_hours(self):
        for slug, job in self.jobs:
            expr = (job.get("schedule") or {}).get("expr") or ""
            with self.subTest(job=job["name"]):
                self.assertEqual(hours_in(expr), set(range(24)).difference(PEAK_HOURS))


class TestScriptJobsAreOutOfScope(unittest.TestCase):
    def test_a_script_job_keeps_its_own_cadence(self):
        for slug, job in live_jobs():
            if job.get("name", "").endswith("tracker-sheets-sync"):
                with self.subTest(job=job["name"]):
                    self.assertTrue(job.get("no_agent"))


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
import ast
ast.parse(P.read_text())
print("written", len(P.read_text()), "chars, parses OK")
