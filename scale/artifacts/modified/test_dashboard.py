#!/usr/bin/env python3
"""Dashboard API tests: run the real server in-process against a scratch tenant.

Two things are asserted everywhere: a read is open and a write is behind the token, and an
outcome is the code path's real result rather than a plausible one. The scheduler CLI is faked by a
shim that records its own argv, so `run a sweep now` can be proven to call the same CLI the engine
does, and the tracker build is a real subprocess in a scratch workspace.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "billing"))

import dashboard.server as dash  # noqa: E402

TOKEN = "test-token"
MONTH = time.strftime("%Y-%m")
OLD_MONTH = "2019-01"
LICENCE_SECRET = "not-a-real-secret-for-tests"
FAKE_TELEGRAM_TOKEN = "1234567890:AAFakeTokenValueForTestsOnly1234567890"
FAKE_EMAIL_KEY = "sk-fakekeyfortests000111"

# What `hermes cron list --all` prints for this profile. Three jobs: two of ours (one active, one
# paused), one belonging to a different tenant that must never be touched.
CRON_LIST = """  7cd96301a65a [active]
    Name:      jane-doe-job-hunt
    Schedule:  every 180m
    Repeat:    forever
    Next run:  2026-09-21T22:14:23+00:00
    Deliver:   local
    Last run:  2026-09-21T19:14:23+00:00  ok
    Dispatch:  on time (scheduled 2026-09-21T19:03:38+00:00)
    Execution: completed  bf03a9eea4be4191a522363d0e932c5d

  aaaaaaaaaaaa [paused]
    Name:      jane-doe-mail
    Schedule:  every 20m
    Next run:  2026-09-21T22:30:00+00:00
    Last run:  2026-09-21T19:20:00+00:00  failed

  bbbbbbbbbbbb [active]
    Name:      other-tenant-job-hunt
    Schedule:  every 60m
    Next run:  2026-09-21T22:30:00+00:00

  cccccccccccc [active]
    Name:      jane-doe-tracker-sheets-sync
    Schedule:  every 360m
    Next run:  2026-09-22T01:30:00+00:00
    Last run:  2026-09-21T19:30:00+00:00  ok
"""

SHIM = '''#!/usr/bin/env python3
"""Stand-in for the scheduler CLI: records its argv, replays a canned answer."""
import json
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
with open(here / "calls.jsonl", "a") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\\n")
if "list" in sys.argv[1:]:
    sys.stdout.write((here / "cronlist.txt").read_text(encoding="utf-8"))
    sys.exit(0)
ctl = json.loads((here / "ctl.json").read_text(encoding="utf-8"))
sys.stdout.write(ctl.get("out", ""))
sys.exit(int(ctl.get("rc", 0)))
'''

TRACKER = '''"""The tenant's row store: rows only, no workbook (the sheet is the tracker)."""

applications = [
    ["1", "Acme", "Data Engineer", "Utrecht, Netherlands", 4.5, "Submitted", "Personio", "Yes", "Yes", "jobs@acme.test", "https://acme.test/jobs/1", "Applied %(month)s-05 via Personio"],
    ["2", "Globex", "Analytics Engineer", "Berlin, Germany", 4.0, "Interview", "Lever", "Yes", "Yes", "-", "https://globex.test/jobs/2", "Screening call %(old)s-09"],
]
headers = ["#", "Company", "Role", "Location", "Fit (/5)", "Status", "ATS/Portal",
           "Tailored CV", "Cover Letter", "HR Email", "Apply URL", "Notes"]
'''

VERIFIER = '''#!/usr/bin/env python3
"""Stand-in for the tenant's tracker verifier: reports the rows it was pointed at."""
import sys

print("verified tracker in", sys.argv[-1])
'''


def _get(url, token=None):
    req = urllib.request.Request(url, headers={"X-Dashboard-Token": token} if token else {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _get_raw(url, token=None):
    req = urllib.request.Request(url, headers={"X-Dashboard-Token": token} if token else {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _post(url, payload, token=None):
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Dashboard-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _post_raw(url, payload, token=None):
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Dashboard-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


class DashboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="jha-dash-"))
        (cls.tmp / "config").mkdir()
        (cls.tmp / "bin").mkdir()
        ws = cls.tmp / "hunts" / "jane-doe"
        (ws / "gates").mkdir(parents=True)
        (ws / "tools").mkdir()
        # a scratch tenant config: the shipped example plus the two billing links an operator sets
        example = (ROOT / "config" / "tenant.example.yaml").read_text(encoding="utf-8")
        cls.cfg_template = example.replace(
            "  usage_reporting: true",
            '  usage_reporting: true\n'
            '  checkout_url: "https://checkout.example.test/session-1"\n'
            '  portal_url: "https://billing.example.test/portal"')
        cls.cfg_path = cls.tmp / "config" / "tenant.yaml"
        (cls.cfg_path).write_text(cls.cfg_template, encoding="utf-8")
        # the tenant's row store: the sheet is the tracker, so no workbook is written anywhere
        (ws / "build_tracker.py").write_text(TRACKER % {"month": MONTH, "old": OLD_MONTH}, encoding="utf-8")
        (ws / "tools" / "verify_tracker.py").write_text(VERIFIER, encoding="utf-8")
        (ws / "tools" / "verify_tracker.py").chmod(0o755)
        # the scheduler shim. A shebang script is only directly executable on POSIX: Windows has no
        # shebang support, so there the fixture writes the same shape the Windows installer ships, a
        # .cmd launcher that hands the arguments to this interpreter (jobhunt-agent.cmd is that
        # shape). Neither branch fakes the CLI: both run the real script in a real subprocess.
        cls.shim = cls.tmp / "bin" / "hermes"
        cls.shim.write_text(SHIM, encoding="utf-8")
        cls.shim.chmod(0o755)
        cls.hermes_cli = cls.shim
        if os.name == "nt":
            cls.hermes_cli = cls.tmp / "bin" / "hermes.cmd"
            cls.hermes_cli.write_text(f"@echo off\r\n\"{sys.executable}\" \"{cls.shim}\" %*\r\n", encoding="utf-8")
        (cls.tmp / "bin" / "cronlist.txt").write_text(CRON_LIST, encoding="utf-8")
        cls.set_ctl(0, "queued for the next tick")
        # a usage meter with one run this month and one last month
        cls.usage_dir = cls.tmp / "usage"
        cls.usage_dir.mkdir()
        (cls.usage_dir / "jane-doe.jsonl").write_text(
            json.dumps({"ts": MONTH + "-10T09:00:00Z", "job": "sweep", "prompt_tokens": 2_500_000,
                        "completion_tokens": 4000, "model": "m", "error": False}) + "\n" +
            json.dumps({"ts": OLD_MONTH + "-10T09:00:00Z", "job": "sweep", "prompt_tokens": 1_000_000,
                        "completion_tokens": 2000, "model": "m", "error": True}) + "\n", encoding="utf-8")
        dash.Handler.cfg_path = cls.cfg_path
        dash.Handler.token = TOKEN
        dash.Handler.index = ROOT / "dashboard" / "index.html"
        cls._orig_ws = dash.workspace_for
        cls._orig_usage = dash.USAGE_DIR
        cls._orig_hermes = dash.HERMES_BIN
        dash.workspace_for = lambda cfg: cls.tmp / "hunts" / (cfg["tenant"]["slug"])
        dash.USAGE_DIR = cls.usage_dir
        dash.HERMES_BIN = str(cls.hermes_cli)
        cls.httpd = dash.Server(("127.0.0.1", 0), dash.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        dash.workspace_for = cls._orig_ws
        dash.USAGE_DIR = cls._orig_usage
        dash.HERMES_BIN = cls._orig_hermes
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def set_ctl(cls, rc: int, out: str) -> None:
        (cls.tmp / "bin" / "ctl.json").write_text(json.dumps({"rc": rc, "out": out}), encoding="utf-8")

    def setUp(self):
        # every test starts from the shipped dials: no test may inherit another test's writes
        self.cfg_path.write_text(self.cfg_template, encoding="utf-8")
        self.clear_calls()

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def clear_calls(self):
        (self.tmp / "bin" / "calls.jsonl").write_text("", encoding="utf-8")

    def calls(self):
        raw = (self.tmp / "bin" / "calls.jsonl").read_text(encoding="utf-8").strip()
        return [json.loads(line) for line in raw.splitlines()] if raw else []

    def cfg_hash(self):
        return hashlib.sha256(self.cfg_path.read_bytes()).hexdigest()

    def cfg_text(self):
        return self.cfg_path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------ the page and liveness
    def test_index_serves_html(self):
        with urllib.request.urlopen(self.url("/"), timeout=10) as r:
            body = r.read().decode()
        self.assertEqual(r.status, 200)
        self.assertIn("jobhunt-agent", body.lower())
        self.assertIn("api/state", body)
        for marker in ("api/overview", "api/config/preview", "api/control/", "api/billing",
                       "api/applications", "api/config/dials", "api/usage"):
            self.assertIn(marker, body, f"the page must expose {marker}")
        # readable on a phone: the viewport must follow the device, not a fixed width
        self.assertIn('name="viewport" content="width=device-width', body)
        self.assertNotIn("width=1200", body)

    def test_healthz(self):
        code, body = _get(self.url("/api/healthz"))
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])

    def test_health_reports_the_row_store_and_the_sheet_payload(self):
        """Row counts per candidate come from the row store the sheet is built from, never a workbook."""
        code, s = _get(self.url("/api/state"))
        self.assertEqual(code, 200)
        self.assertTrue(s["health"]["row_store_present"], s["health"])
        self.assertEqual(s["health"]["rows"], 2, s["health"])
        self.assertIn("sheet", s["health"])
        self.assertNotIn("tracker_present", s["health"])
        # a sync stamp stands in for a real push: the panel reports it rather than assuming
        state = self.tmp / "hunts" / "jane-doe" / "data" / "ops"
        state.mkdir(parents=True, exist_ok=True)
        (state / "sheets_sync_stamp.json").write_text(json.dumps(
            {"utc": "2026-09-21T21:00:00Z", "rows": 3, "sheet": "test-sheet-id"}), encoding="utf-8")
        (state / "tracker_export.json").write_text(json.dumps({"jane-doe": {
            "title": "t", "sheet_name": "Applications", "rows_store": "x",
            "rows": [["#", "Company"], ["1", "Acme"], ["2", "Globex"]],
            "row_store": str(self.tmp / "hunts" / "jane-doe" / "build_tracker.py")}}), encoding="utf-8")
        try:
            code, s = _get(self.url("/api/state"))
            self.assertEqual(code, 200)
            sheet = s["health"]["sheet"]
            self.assertEqual(sheet["rows"], 3)
            self.assertEqual(sheet["data_rows"], 2)
            self.assertEqual(sheet["in_sync"], True, sheet)
            self.assertEqual(sheet["last_push_utc"], "2026-09-21T21:00:00Z")
        finally:
            (state / "tracker_export.json").unlink(missing_ok=True)
            (state / "sheets_sync_stamp.json").unlink(missing_ok=True)

    def test_state_shape(self):
        code, s = _get(self.url("/api/state"))
        self.assertEqual(code, 200)
        for key in ("tenant", "dials", "plan", "counts", "recent", "usage", "jobs", "health"):
            self.assertIn(key, s)
        self.assertEqual(s["counts"].get("Submitted"), 1)
        self.assertEqual(s["counts"].get("Interview"), 1)
        self.assertEqual(s["total_rows"], 2)
        self.assertEqual(s["tenant"]["slug"], "jane-doe")
        self.assertNotIn("@", s["tenant"]["email_masked"].split("@")[0], "local part must be masked")

    def test_state_never_leaks_secrets_or_mail(self):
        """No credential, key or mail setting may appear - only counts, statuses and the dials.

        Token COUNTS are fine (prompt_tokens is a quantity); token VALUES are not, so this checks the
        secret-bearing key names and the shapes of real credentials.
        """
        _, s = _get(self.url("/api/state"))
        blob = json.dumps(s).lower()
        for forbidden in ("password", "app_password", "smtp", "imap", "api_key", "apikey",
                          "licence_key", "license_key", "bot_token", "secret", "credential"):
            self.assertNotIn(forbidden, blob, f"{forbidden!r} must not appear in /api/state")
        import re as _re
        for pattern, what in ((r"\d{8,10}:aa[a-z0-9_-]{30,}", "telegram bot token"),
                              (r"sk-[a-z0-9]{16,}", "model api key"),
                              (r"whsec_[a-z0-9]{10,}", "stripe webhook secret")):
            self.assertIsNone(_re.search(pattern, blob), f"{what} value leaked into /api/state")

    # ------------------------------------------------------------------ applications
    def test_applications_filter(self):
        code, body = _get(self.url("/api/applications?status=Interview"))
        self.assertEqual(code, 200)
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["rows"][0]["company"], "Globex")

    def test_applications_search_covers_company_role_and_notes(self):
        for query, company in (("acme", "Acme"), ("analytics", "Globex"), ("personio", "Acme")):
            code, body = _get(self.url(f"/api/applications?q={query}"))
            self.assertEqual(code, 200, body)
            self.assertEqual([r["company"] for r in body["rows"]], [company], query)
        code, body = _get(self.url("/api/applications?q=nothing-matches-this"))
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["total"], 2, "the unfiltered total must still be reported")

    def test_application_detail_has_dates_notes_and_url(self):
        code, body = _get(self.url("/api/applications/1"))
        self.assertEqual(code, 200, body)
        row = body["row"]
        self.assertEqual(row["company"], "Acme")
        self.assertEqual(row["status"], "Submitted")
        self.assertEqual(body["key_dates"], [f"{MONTH}-05"])
        self.assertIn("Applied", body["notes"])
        self.assertEqual(body["apply_url"], "https://acme.test/jobs/1")
        code, body = _get(self.url("/api/applications/9999"))
        self.assertEqual(code, 404)

    # ------------------------------------------------------------------ overview
    def test_overview_reports_a_live_hunt_and_every_job(self):
        code, o = _get(self.url("/api/overview"))
        self.assertEqual(code, 200, o)
        hunt = o["hunt"]
        self.assertTrue(hunt["live"], "one job is active, so the hunt is live")
        self.assertEqual(hunt["jobs_active"], 2, "the sweep and the tenant's sheets job")
        self.assertEqual(hunt["jobs_total"], 3, "the other tenant's job is not this hunt")
        self.assertEqual(hunt["jobs_on_host"], 4)
        self.assertEqual(hunt["sweep_job"], "jane-doe-job-hunt")
        names = [j["name"] for j in hunt["jobs"]]
        self.assertEqual(sorted(names), ["jane-doe-job-hunt", "jane-doe-mail",
                                         "jane-doe-tracker-sheets-sync"],
                         "another tenant's job must never appear")
        mine = next(j for j in hunt["jobs"] if j["name"] == "jane-doe-job-hunt")
        self.assertEqual(mine["schedule"], "every 180m")
        self.assertEqual(mine["last_outcome"], "ok")
        self.assertEqual(mine["last_run"], "2026-09-21T19:14:23+00:00")
        self.assertEqual(mine["next_run"], "2026-09-21T22:14:23+00:00")
        paused = next(j for j in hunt["jobs"] if j["name"] == "jane-doe-mail")
        self.assertEqual(paused["state"], "paused")
        self.assertEqual(paused["last_outcome"], "failed")
        self.assertEqual(o["counts"]["Submitted"], 1)
        self.assertEqual(o["total_rows"], 2)

    def test_overview_counts_applications_this_month(self):
        _, o = _get(self.url("/api/overview"))
        apps = o["applications"]
        self.assertEqual(apps["month"], MONTH)
        self.assertEqual(apps["this_month"], 1, "only the row dated this month counts")
        self.assertEqual(apps["applied_total"], 2)
        self.assertEqual(apps["undated"], 0)
        self.assertEqual(apps["by_month"][MONTH], 1)

    def test_overview_action_row_is_everything_and_token_gated(self):
        _, o = _get(self.url("/api/overview"))
        actions = {a["id"]: a for a in o["actions"]}
        for wanted in ("sweep", "pause", "resume", "alert-test", "sheet-sync", "billing"):
            self.assertIn(wanted, actions, f"the action row must offer {wanted}")
        for a in actions.values():
            if a["method"] == "POST":
                self.assertTrue(a["token_required"], f"{a['id']} writes, so it needs the token")
            self.assertTrue(a["url"].startswith("/api/"))

    # ------------------------------------------------------------------ cost and usage
    def test_usage_reports_measured_spend_and_the_monthly_allowance(self):
        code, u = _get(self.url("/api/usage"))
        self.assertEqual(code, 200, u)
        self.assertEqual(u["runs"], 2, "lifetime runs")
        self.assertEqual(u["plan"], "pro", "the plan comes from this tenant's config")
        self.assertEqual(u["includes_runs"], 420)
        month = u["this_month"]
        self.assertEqual(month["runs"], 1, "the older line is outside the window")
        self.assertEqual(month["errors"], 0)
        self.assertGreater(month["spend"], 0)
        self.assertEqual(u["runs_remaining"], 419)
        self.assertEqual(month["runs_remaining"], 419)
        self.assertGreater(month["per_run_cost"], 0)
        self.assertEqual(month["overage_runs"], 0)
        self.assertEqual(month["overage_cost"], 0.0)
        self.assertEqual(u["plan_limits"]["sweep_interval_minutes"], 360)
        self.assertIn("rates", u)
        self.assertEqual(month["sweeps"], 1)

    def test_cost_route_answers_with_the_same_figures(self):
        _, a = _get(self.url("/api/usage"))
        code, b = _get(self.url("/api/cost"))
        self.assertEqual(code, 200)
        self.assertEqual(a, b, "/api/cost is the cost panel's name for /api/usage")

    # ------------------------------------------------------------------ billing
    def test_billing_state_carries_the_checkout_link_and_invoice_route(self):
        code, b = _get(self.url("/api/billing"))
        self.assertEqual(code, 200, b)
        self.assertEqual(b["plan"], "pro")
        self.assertEqual(b["plan_name"], "Pro")
        self.assertEqual(b["price_usd_month"], 70)
        self.assertEqual(len(b["plans"]), 3)
        self.assertTrue(b["checkout"]["configured"])
        self.assertEqual(b["checkout"]["url"], "https://checkout.example.test/session-1")
        self.assertIn("stripe_checkout.py", b["checkout"]["command"])
        self.assertEqual(b["invoices"]["portal_url"], "https://billing.example.test/portal")
        self.assertIn("receipt", b["invoices"]["how"].lower())

    def test_billing_licence_state_reports_the_key_state_never_the_key(self):
        """A licence key is a credential: the route may say present/valid/expiry, and nothing else."""
        from license import issue, verify  # billing/license.py, loaded by path in the server too

        key = issue("jane-doe", "pro", days=10, runs=420, secret=LICENCE_SECRET)
        self.cfg_path.write_text(self.cfg_template.replace(
            '  license_key: ""', f'  license_key: "{key}"'), encoding="utf-8")
        os.environ["LICENCE_SECRET"] = LICENCE_SECRET
        try:
            code, text = _get_raw(self.url("/api/billing"))
            self.assertEqual(code, 200, text)
            self.assertNotIn(key, text, "the licence key must never be returned")
            body = json.loads(text)
            lic = body["licence"]
            self.assertTrue(lic["present"])
            self.assertTrue(lic["valid"])
            self.assertTrue(lic["verified"])
            self.assertEqual(lic["plan"], "pro")
            self.assertEqual(lic["runs"], 420)
            self.assertGreaterEqual(lic["days_left"], 9)
            self.assertEqual(lic["expires"], time.strftime(
                "%Y-%m-%d", time.gmtime(time.time() + 10 * 86400)))
        finally:
            os.environ.pop("LICENCE_SECRET", None)
        # an expired key is reported as invalid rather than treated as fine
        expired = issue("jane-doe", "pro", days=-30, secret=LICENCE_SECRET)
        ok, reason, payload = verify(expired, secret=LICENCE_SECRET, grace_days=0)
        self.assertFalse(ok)
        self.assertIn("expired", reason)
        state = dash.licence_state({"billing": {"license_key": expired}}, secret=LICENCE_SECRET)
        self.assertTrue(state["present"])
        self.assertFalse(state["valid"])
        self.assertNotIn(expired, json.dumps(state))
        # a malformed key is refused, not crashed on
        state = dash.licence_state({"billing": {"license_key": "JHA1.not-base64.not-a-sig"}})
        self.assertTrue(state["present"])
        self.assertFalse(state["valid"])
        self.assertIsNone(dash.licence_state({"billing": {"license_key": ""}})["plan"] or None)

    # ------------------------------------------------------------------ configuration dials
    def test_dials_route_names_what_is_writable_and_what_is_not(self):
        code, d = _get(self.url("/api/config/dials"))
        self.assertEqual(code, 200, d)
        for dial in ("countries", "roles", "salary", "cadence", "quiet_hours", "alert_thresholds"):
            self.assertIn(dial, d)
        for field in ("countries", "roles", "salary", "schedule.sweep", "quiet_hours", "ping_on"):
            self.assertIn(field, d["writable"])
        self.assertIn("billing.plan", d["operator_only"])
        self.assertEqual(d["countries"]["options"], sorted(d["countries"]["options"]))
        self.assertIn("NL", d["countries"]["options"])
        self.assertNotIn("GB", d["countries"]["options"], "the scope is EU-only")
        self.assertIn("EU", d["countries"]["rule"])
        self.assertEqual(d["cadence"]["plan_allowed"], "every 360m")
        self.assertEqual(d["quiet_hours"]["current"], ["22:00", "07:00"])
        self.assertEqual(d["alert_thresholds"]["current"], ["interview_invite", "offer", "action_required"])

    def test_config_preview_shows_the_diff_and_writes_nothing(self):
        before = self.cfg_hash()
        payload = {"salary": {"target_floor": 4300, "ask_range": [4500, 5200]},
                   "ping_on": ["offer", "action_required"],
                   "quiet_hours": ["22:30", "06:30"]}
        code, body = _post(self.url("/api/config/preview"), payload)     # no token: a preview is a read
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertFalse(body["refused"])
        self.assertFalse(body["written"])
        fields = [c["field"] for c in body["changes"]]
        self.assertIn("salary", fields)
        self.assertIn("quiet_hours", fields)
        self.assertIn("ping_on", fields)
        self.assertEqual(self.cfg_hash(), before, "a preview may not touch the file")

    def test_non_eu_country_is_refused_and_the_file_never_changes(self):
        before = self.cfg_hash()
        code, body = _post(self.url("/api/config"),
                           {"countries": {"primary": ["GB"], "secondary": [], "rotation": []}},
                           token=TOKEN)
        self.assertEqual(code, 400)
        self.assertFalse(body["ok"])
        self.assertTrue(body["refused"])
        self.assertIn("EU", body["message"])
        self.assertEqual(self.cfg_hash(), before, "a refused change must leave the file byte-identical")
        # the preview of the same change says so too, and still writes nothing
        code, body = _post(self.url("/api/config/preview"),
                           {"countries": {"primary": ["GB"], "secondary": [], "rotation": []}})
        self.assertEqual(code, 200)
        self.assertTrue(body["refused"])
        self.assertIn("EU", body["errors"][0])
        self.assertEqual(self.cfg_hash(), before)

    def test_refused_salary_and_quiet_hours_changes_leave_the_file_identical(self):
        before = self.cfg_hash()
        cases = [
            ({"salary": {"target_floor": 5000, "ask_range": [4500, 5200]}},
             "ask range below the floor"),
            ({"salary": {"current_gross": "lots"}}, "not a number"),
            ({"quiet_hours": ["25:00", "07:00"]}, "an impossible hour"),
            ({"quiet_hours": ["22:00"]}, "only one end"),
            ({"ping_on": []}, "no thresholds left"),
            ({"roles": []}, "no roles left"),
            ({"schedule.sweep": "every 5 minutes"}, "a cadence the plan cannot express"),
        ]
        for payload, why in cases:
            code, body = _post(self.url("/api/config"), payload, token=TOKEN)
            self.assertEqual(code, 400, f"{why} must be refused: {body}")
            self.assertFalse(body["ok"], why)
            self.assertFalse(body["written"], why)
            self.assertEqual(self.cfg_hash(), before, f"{why} changed the file")

    def test_config_write_applies_the_new_dials(self):
        code, body = _post(self.url("/api/config"),
                           {"quiet_hours": ["22:30", "06:30"],
                            "ping_on": ["offer", "action_required"],
                            "schedule.sweep": "every 360m"},
                           token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["written"], body)
        text = self.cfg_text()
        self.assertIn('["22:30", "06:30"]', text)
        self.assertIn('["offer", "action_required"]', text)
        self.assertIn('"every 360m"', text)
        # and a faster cadence than the plan allows is a warning, not a silent charge
        code, body = _post(self.url("/api/config"), {"schedule.sweep": "every 60m"}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(any("faster than the plan" in w for w in body["warnings"]), body)

    def test_config_write_requires_token(self):
        code, body = _post(self.url("/api/config"), {"roles": ["Data Engineer"]})
        self.assertEqual(code, 401)
        self.assertIn("unauthorised", body["error"])

    def test_config_write_applies_and_regenerates_scope(self):
        code, body = _post(self.url("/api/config"),
                           {"countries": {"primary": ["NL"], "secondary": ["DE", "IE"],
                                          "rotation": ["SE", "DK"]},
                            "roles": ["Data Engineer", "Analytics Engineer"],
                            "salary": {"current_gross": 3400, "target_floor": 4200,
                                       "ask_range": [4500, 5200]},
                            "schedule.sweep": "every 360m"},
                           token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        text = (self.tmp / "config" / "tenant.yaml").read_text(encoding="utf-8")
        self.assertIn('"DE", "IE"', text)
        self.assertIn("current_gross: 3400", text)
        self.assertIn("[4500, 5200]", text)
        self.assertIn('every 360m', text)
        # the roles dial is a block list in the shipped config: it must really be rewritten
        self.assertIn("Analytics Engineer", text)
        self.assertNotIn("Snowflake Engineer", text, "the old role list must be replaced, not appended")
        # the scope file must follow the dials
        from provisioning.provision_tenant import read_config
        cfg = read_config(self.tmp / "config" / "tenant.yaml")
        self.assertEqual(cfg["targeting"]["countries"]["secondary"], ["DE", "IE"])

    # ------------------------------------------------------------------ the model budget
    def test_the_budget_dial_is_writable_and_reaches_the_file_a_sweep_reads(self):
        """A dial the subscriber can SEE is a dial they must be able to CHANGE, and it has to travel.

        Same shape as the backoff dial's tests: the config is the source of truth, and the workspace copy
        is what an unattended run can actually read.
        """
        before = self.cfg_hash()
        code, body = _post(self.url("/api/config"),
                           {"budget": {"daily_usd": 2.5, "on_exceed": "stop"}}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertIn("daily_usd: 2.50", self.cfg_text())
        self.assertIn("on_exceed: stop", self.cfg_text())
        self.assertEqual([c["field"] for c in body["changes"]], ["budget"])
        from provisioning.provision_tenant import read_config
        self.assertEqual(read_config(self.cfg_path)["budget"]["daily_usd"], 2.5)
        carried = json.loads((self.tmp / "hunts" / "jane-doe" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(carried["budget"]["on_exceed"], "stop",
                         "the dial must reach the file the unattended sweep reads")
        self.assertNotEqual(before, self.cfg_hash())

    def test_a_refused_budget_value_leaves_the_config_byte_identical(self):
        before = self.cfg_hash()
        for bad in ({"on_exceed": "explode"}, {"daily_usd": 0}, {"daily_usd": "lots"}):
            with self.subTest(payload=bad):
                code, body = _post(self.url("/api/config"), {"budget": bad}, token=TOKEN)
                self.assertEqual(code, 400, body)
                self.assertFalse(body["ok"])
                self.assertEqual(self.cfg_hash(), before, "a refused dial may not touch the file")

    def test_the_dials_route_reports_the_budget_and_its_allowed_values(self):
        code, d = _get(self.url("/api/config/dials"))
        self.assertEqual(code, 200, d)
        self.assertIn("budget", d["writable"])
        self.assertEqual(d["budget"]["options"], ["warn", "throttle", "stop"])
        self.assertEqual(d["budget"]["current"]["daily_usd"], 1.0)
        self.assertIn("daily_usd", d["budget"]["default"])

    def test_the_alerts_payload_carries_today_s_spend_and_the_dial(self):
        code, body = _get(self.url("/api/alerts"))
        self.assertEqual(code, 200, body)
        budget = body["budget"]
        self.assertIsNotNone(budget, "the alerts view must be able to show what today cost")
        self.assertIn("spent_today_usd", budget)
        self.assertEqual(budget["budget"]["daily_usd"], 1.0)
        self.assertIn("volume", budget, "the payload carries the volume the gate would allow")

    def test_scope_regeneration_failure_rolls_the_config_back(self):
        """Half-applied is worse than not applied: if the scope file cannot follow, nothing sticks."""
        before = self.cfg_hash()
        scope = self.tmp / "hunts" / "jane-doe" / "eu_scope.json"
        original_ws = dash.workspace_for
        # The scope write must really fail. A path under a regular file cannot be created anywhere
        # (ENOTDIR on POSIX, ERROR_PATH_NOT_FOUND on Windows), unlike a chmod-ed directory, which
        # Windows ignores because it has no POSIX write bit.
        dash.workspace_for = lambda cfg: self.cfg_path / "definitely-not-writable" / "jane-doe"
        try:
            code, body = _post(self.url("/api/config"), {"schedule.sweep": "every 60m"}, token=TOKEN)
        finally:
            dash.workspace_for = original_ws
            if scope.exists():
                scope.unlink()
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"])
        self.assertIn("rolled back", body["message"])
        self.assertEqual(self.cfg_hash(), before)

    # ------------------------------------------------------------------ one-click controls
    def test_control_sweep_uses_the_scheduler_cli(self):
        self.clear_calls()
        code, body = _post(self.url("/api/control/sweep"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertIn("queued for the next tick", body["message"])
        self.assertEqual(self.calls()[-1], ["-p", "jane-doe", "cron", "run", "jane-doe-job-hunt"],
                         "the sweep must go through the same CLI the engine schedules with")

    def test_control_sweep_reports_the_real_failure(self):
        self.set_ctl(3, "no such job: jane-doe-job-hunt")
        try:
            code, body = _post(self.url("/api/control/sweep"), {}, token=TOKEN)
        finally:
            self.set_ctl(0, "queued for the next tick")
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"], "a failed queue attempt must never report ok")
        self.assertIn("no such job", body["message"])
        self.assertEqual(body["detail"]["rc"], 3)

    def test_control_sweep_says_so_when_the_cli_is_missing(self):
        original = dash.HERMES_BIN
        dash.HERMES_BIN = "/nonexistent/hermes"
        try:
            code, body = _post(self.url("/api/control/sweep"), {}, token=TOKEN)
        finally:
            dash.HERMES_BIN = original
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"])
        self.assertIn("not on this host", body["message"])

    def test_control_pause_and_resume_touch_only_this_tenants_jobs(self):
        self.clear_calls()
        code, body = _post(self.url("/api/control/pause"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertEqual(sorted(body["detail"]["jobs"]),
                         ["jane-doe-job-hunt", "jane-doe-mail", "jane-doe-tracker-sheets-sync"])
        called = self.calls()
        self.assertIn(["-p", "jane-doe", "cron", "pause", "jane-doe-job-hunt"], called)
        self.assertIn(["-p", "jane-doe", "cron", "pause", "jane-doe-mail"], called)
        self.assertFalse([c for c in called if "other-tenant" in " ".join(c)],
                         "another tenant's job must never be paused")
        self.clear_calls()
        code, body = _post(self.url("/api/control/resume"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertIn(["-p", "jane-doe", "cron", "resume", "jane-doe-job-hunt"], self.calls())

    def test_control_pause_reports_a_refusal_from_the_scheduler(self):
        self.set_ctl(2, "job is already paused")
        try:
            code, body = _post(self.url("/api/control/pause"), {"job": "jane-doe-mail"}, token=TOKEN)
        finally:
            self.set_ctl(0, "queued for the next tick")
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"])
        self.assertIn("already paused", body["message"])

    def test_job_toggle_route_still_works(self):
        self.clear_calls()
        code, body = _post(self.url("/api/jobs/jane-doe-mail/pause"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertEqual(self.calls()[-1], ["-p", "jane-doe", "cron", "pause", "jane-doe-mail"])
        self.assertEqual(body["message"], "queued for the next tick")

    def test_control_sheet_sync_runs_the_profile_sheets_job(self):
        """Sync the sheet now: the profile's own job does the push, so the dashboard runs that job."""
        self.clear_calls()
        code, body = _post(self.url("/api/control/sheet-sync"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertEqual(body["detail"]["job"], "jane-doe-tracker-sheets-sync")
        self.assertIn(["-p", "jane-doe", "cron", "run", "jane-doe-tracker-sheets-sync"], self.calls())
        self.assertNotIn(["-p", "jane-doe", "cron", "run", "jane-doe-job-hunt"], self.calls(),
                         "syncing the sheet must not queue a sweep")

    def test_sheet_sync_reports_a_scheduler_refusal(self):
        self.set_ctl(2, "no such job")
        try:
            code, body = _post(self.url("/api/control/sheet-sync"), {}, token=TOKEN)
        finally:
            self.set_ctl(0, "queued for the next tick")
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"])
        self.assertIn("refused to queue", body["message"])

    def test_the_workbook_rebuild_control_is_gone(self):
        code, body = _post(self.url("/api/control/tracker-sync"), {}, token=TOKEN)
        self.assertEqual(code, 404, body)
        _, o = _get(self.url("/api/overview"))
        ids = {a["id"] for a in o["actions"]}
        self.assertIn("sheet-sync", ids)
        self.assertNotIn("tracker-sync", ids)

    def test_control_channels_switches_and_a_bad_channel_changes_nothing(self):
        code, body = _post(self.url("/api/control/channels"), {"channels": ["local", "telegram"]},
                           token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertIn("channels: [local, telegram]", self.cfg_text())
        before = self.cfg_hash()
        code, body = _post(self.url("/api/control/channels"), {"channels": ["carrier-pigeon"]},
                           token=TOKEN)
        self.assertEqual(code, 400, body)
        self.assertFalse(body["ok"])
        self.assertEqual(self.cfg_hash(), before, "a refused channel list must change no file")
        code, body = _post(self.url("/api/control/channels"), {"channels": []}, token=TOKEN)
        self.assertEqual(code, 400)
        self.assertEqual(self.cfg_hash(), before)

    def test_control_alert_test_delivers_through_the_notifier(self):
        code, body = _post(self.url("/api/control/alert-test"),
                           {"channel": "local", "dry_run": True}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"], body)
        self.assertIn("local", body["detail"]["results"])
        self.assertEqual(body["detail"]["results"]["local"]["ok"], True)
        # the legacy route answers with the same code path and its own shape
        code, body = _post(self.url("/api/notify/test"),
                           {"channel": "local", "dry_run": True}, token=TOKEN)
        self.assertEqual(code, 200, body)
        self.assertTrue(body["ok"])
        self.assertIn("results", body)

    # ------------------------------------------------------------------ guards
    def test_every_write_route_is_401_without_the_token(self):
        _, o = _get(self.url("/api/overview"))
        writes = [a["url"] for a in o["actions"] if a["method"] == "POST"]
        writes += ["/api/config", "/api/notify/test", "/api/notify/channels",
                   "/api/jobs/jane-doe-job-hunt/resume", "/api/jobs/jane-doe-job-hunt/pause"]
        self.assertGreaterEqual(len(writes), 9)
        before = self.cfg_hash()
        for url in writes:
            code, body = _post(self.url(url), {})
            self.assertEqual(code, 401, f"{url} answered {code} without a token: {body}")
            self.assertIn("unauthorised", body["error"])
        self.assertEqual(self.cfg_hash(), before, "an unauthorised write touched the config")

    def test_reads_are_open(self):
        for path in ("/api/healthz", "/api/state", "/api/overview", "/api/applications",
                     "/api/applications/1", "/api/usage", "/api/cost", "/api/billing",
                     "/api/config/dials", "/api/config", "/api/control", "/api/notify"):
            code, _body = _get(self.url(path))
            self.assertEqual(code, 200, f"{path} must answer without a token")

    def test_no_route_returns_a_secret(self):
        """Every route, with a live token, a licence key and real-looking credentials in the env."""
        from license import issue

        key = issue("jane-doe", "pro", days=5, secret=LICENCE_SECRET)
        self.cfg_path.write_text(self.cfg_template.replace(
            '  license_key: ""', f'  license_key: "{key}"'), encoding="utf-8")
        saved = {k: os.environ.get(k) for k in ("TELEGRAM_BOT_TOKEN", "EMAIL_API_KEY",
                                                "LICENCE_SECRET")}
        os.environ["TELEGRAM_BOT_TOKEN"] = FAKE_TELEGRAM_TOKEN
        os.environ["EMAIL_API_KEY"] = FAKE_EMAIL_KEY
        os.environ["LICENCE_SECRET"] = LICENCE_SECRET
        try:
            bodies = {}
            for path in ("/api/healthz", "/api/state", "/api/overview", "/api/applications",
                         "/api/applications/1", "/api/usage", "/api/cost", "/api/billing",
                         "/api/config/dials", "/api/config", "/api/control", "/api/notify", "/"):
                bodies[path] = _get_raw(self.url(path))[1]
            for path, payload in (("/api/config/preview", {}),
                                  ("/api/config", {}),
                                  ("/api/control/sweep", {}),
                                  ("/api/control/pause", {"job": "jane-doe-job-hunt"}),
                                  ("/api/control/resume", {"job": "jane-doe-job-hunt"}),
                                  ("/api/control/sheet-sync", {}),
                                  ("/api/control/alert-test", {"channel": "local", "dry_run": True}),
                                  ("/api/notify/test", {"channel": "local", "dry_run": True}),
                                  ("/api/control/channels", {"channels": ["telegram"]}),
                                  ("/api/jobs/jane-doe-job-hunt/resume", {})):
                bodies["POST " + path] = _post_raw(self.url(path), payload, token=TOKEN)[1]
            for name, text in bodies.items():
                self.assertNotIn(key, text, f"{name} returned the licence key")
                self.assertNotIn(FAKE_TELEGRAM_TOKEN, text, f"{name} returned the bot token")
                self.assertNotIn(FAKE_EMAIL_KEY, text, f"{name} returned the mail key")
                self.assertNotIn(TOKEN, text, f"{name} returned the dashboard token")
                self.assertIsNone(__import__("re").search(r"JHA1\.[A-Za-z0-9_=-]{6,}", text),
                                  f"{name} returned a licence-shaped value")
            # and the guard is testing something real: the presence booleans must be true
            summary = json.loads(bodies["/api/notify"])
            self.assertTrue(summary["telegram"]["token_present"], "the fake bot token must be seen")
            self.assertTrue(summary["email"]["api_key_present"], "the fake mail key must be seen")
            self.assertTrue(json.loads(bodies["/api/billing"])["licence"]["present"])
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_existing_routes_still_answer(self):
        for path in ("/api/state", "/api/applications", "/api/config", "/api/usage", "/api/notify"):
            code, _ = _get(self.url(path))
            self.assertEqual(code, 200, path)
        for path, payload in (("/api/notify/test", {"channel": "local", "dry_run": True}),
                              ("/api/notify/channels", {"channels": ["telegram"]})):
            code, body = _post(self.url(path), payload, token=TOKEN)
            self.assertEqual(code, 200, f"{path}: {body}")
        code, body = _post(self.url("/api/jobs/jane-doe-job-hunt/resume"), {}, token=TOKEN)
        self.assertEqual(code, 200, body)
        with urllib.request.urlopen(self.url("/"), timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("jobhunt-agent", r.read().decode().lower())

    def test_bad_job_name_is_refused(self):
        code, body = _post(self.url("/api/jobs/..%2Fetc%2Fpasswd/resume"), {}, token=TOKEN)
        self.assertIn(code, (400, 404))

    def test_unknown_route_404(self):
        code, _ = _get(self.url("/api/nope"))
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
