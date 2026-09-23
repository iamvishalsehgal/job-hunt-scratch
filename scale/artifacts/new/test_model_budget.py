#!/usr/bin/env python3
"""The per-account model budget: the arithmetic, the ledger, the degrade paths - and the fact that both
the subscriber and the operator can see the spend.

The blocker these tests exist for, in the product's own words, was "no per-account model budget": one
tenant's sweeps could spend without limit and no surface anywhere said what an account had cost. Two
claims therefore have to stay true, and most of this file guards them rather than the happy path:

  1. a budget can never CRASH or SILENTLY SLOW an unattended run. A missing, truncated or hand-edited
     dial degrades to the built-in default, says so, and changes nothing about the run's volume;
  2. the number the gate enforces against is the number the subscriber is shown. One ledger, one cost
     model, one set of dials - the tests compare the gate's arithmetic with tools/price_model.py's, and
     the gate's ledger path with the ops path accessor, instead of trusting two copies of a formula.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATES = ROOT / "engine" / "gates"
sys.path.insert(0, str(GATES))
sys.path.insert(0, str(ROOT))

import model_budget as mb  # noqa: E402

GATE = GATES / "model_budget.py"
SERVER = ROOT / "dashboard" / "server.py"
APP_JS = ROOT / "dashboard" / "app" / "app.js"
CONFIG = ROOT / "config" / "tenant.example.yaml"
TEMPLATE = ROOT / "engine" / "cron" / "jobs.template.json"
PROFILES = pathlib.Path.home() / ".hermes" / "profiles"


def spec(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


def cli(*args):
    r = subprocess.run([sys.executable, str(GATE), *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="jha-budget-"))
        self.ws = self.tmp / "workspace"
        (self.ws / "gates").mkdir(parents=True)
        self.ledger = self.ws / "data" / "usage.jsonl"

    def dial(self, block, name="config.json"):
        (self.ws / name).write_text(json.dumps(block) + "\n", encoding="utf-8")

    def spend(self, usd, day=None, prompt=4_203_926, run_id="r"):
        day = day or mb.spend_today(self.ledger)["day"]
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": f"{day}T09:00:00Z", "run_id": run_id, "prompt_tokens": prompt,
                                 "completion_tokens": 1000, "cost_usd": usd}) + "\n")


# ------------------------------------------------------------------ the arithmetic
class TestTheArithmetic(unittest.TestCase):
    def test_the_cost_model_is_the_products_one_and_not_a_second_copy(self):
        """Two copies of one formula is a drift risk; this is the assertion that stops the drift."""
        pm = spec("jha_price_model_probe", ROOT / "tools" / "price_model.py")
        self.assertEqual(mb.RATES, pm.RATES)
        self.assertAlmostEqual(mb.CACHE_HIT_RATIO, pm.CACHE_HIT_RATIO)
        for pt, ct in ((4_203_926, 51_649), (1_100_000, 19_000), (0, 0), (9_999_999, 250_000),
                       (123, 4)):
            with self.subTest(prompt=pt):
                self.assertAlmostEqual(mb.run_cost(pt, ct), pm.run_cost(pt, ct), places=12)

    def test_a_real_sweep_costs_about_what_the_price_model_says(self):
        """The documented fallback basis (19 Sep 2026 rebuild): a sweep $0.1293, a mailbox run $0.0349.

        tools/price_model.py prices a real mailbox run at $0.0103 because a logged one is cheaper than
        this fallback's token counts; either way the arithmetic must be the same one.
        """
        self.assertAlmostEqual(mb.run_cost(4_203_926, 51_649), 0.1293, places=3)
        self.assertAlmostEqual(mb.run_cost(1_100_000, 19_000), 0.0349, places=3)

    def test_a_throttle_matches_the_interview_backoffs_cap_arithmetic(self):
        """One product, one way of cutting a cap: the two gates must not round differently."""
        sys.path.insert(0, str(GATES))
        import interview_backoff as ib

        for cap in (1, 2, 4, 10, 20, 40):
            for rate in (0.4, 0.25, 0.5, 1.0):
                self.assertEqual(mb.volume_for(cap, "throttle", rate), ib.effective_cap(cap, rate, True),
                                 f"cap {cap} at {rate}")

    def test_a_throttle_never_looks_like_a_stopped_hunt(self):
        for cap in (1, 2, 3, 4, 10):
            self.assertGreaterEqual(mb.volume_for(cap, "throttle", 0.25), 1)

    def test_only_stop_returns_zero(self):
        self.assertEqual(mb.volume_for(10, "stop", 0.25), 0)
        self.assertEqual(mb.volume_for(10, "warn", 0.25), 10)
        self.assertEqual(mb.volume_for(10, "ok", 0.25), 10)
        self.assertEqual(mb.volume_for(0, "ok", 0.25), 0)

    def test_a_nonsense_rate_falls_back_rather_than_dividing_by_zero(self):
        for bad in (0, -1, 2, "x", None):
            with self.subTest(rate=bad):
                self.assertGreaterEqual(mb.volume_for(10, "throttle", bad), 1)

    def test_the_run_kind_is_classified_the_way_the_dashboard_classifies_it(self):
        self.assertEqual(mb.kind_for(4_203_926), "sweep")
        self.assertEqual(mb.kind_for(1_100_000), "mail")
        self.assertEqual(mb.kind_for(500), "run")


# ------------------------------------------------------------------ the ledger
class TestTheLedger(Scratch):
    def test_a_recorded_run_carries_everything_the_ledger_promises(self):
        result = mb.record(workspace=self.ws, tokens_in=4_203_926, tokens_out=51_649,
                           run_id="run-1", job="jane-doe-job-hunt", slug="jane-doe")
        self.assertTrue(result["recorded"])
        line = json.loads(self.ledger.read_text(encoding="utf-8").strip())
        for field in ("ts", "slug", "run_id", "job", "kind", "model", "prompt_tokens",
                      "completion_tokens", "total_tokens", "runs", "cost_usd"):
            self.assertIn(field, line, f"the ledger line must carry {field}")
        self.assertEqual(line["slug"], "jane-doe")
        self.assertEqual(line["kind"], "sweep")
        self.assertAlmostEqual(line["cost_usd"], 0.129305, places=5)

    def test_the_ledger_names_the_account_and_not_the_directory(self):
        """Every provisioned workspace is called `workspace`, so the folder name files everyone together."""
        ws = self.tmp / "profiles" / "jane-doe" / "workspace"
        ws.mkdir(parents=True)
        mb.record(workspace=ws, tokens_in=1000, tokens_out=10, run_id="named")
        line = json.loads((ws / "data" / "usage.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(line["slug"], "jane-doe")

    def test_the_same_run_is_never_counted_twice(self):
        """A re-run, a retry or a cron overlap must not double the account's measured spend."""
        mb.record(workspace=self.ws, tokens_in=4_203_926, tokens_out=51_649, run_id="run-1")
        again = mb.record(workspace=self.ws, tokens_in=4_203_926, tokens_out=51_649, run_id="run-1")
        self.assertFalse(again["recorded"])
        self.assertEqual(len(self.ledger.read_text(encoding="utf-8").strip().splitlines()), 1)

    def test_todays_spend_sums_only_today(self):
        self.spend(0.10, "2026-09-21")
        self.spend(0.25, "2026-09-22", run_id="r2")
        self.spend(0.05, "2026-09-22", run_id="r3")
        today = mb.spend_today(self.ledger, "2026-09-22")
        self.assertEqual(today["runs"], 2)
        self.assertAlmostEqual(today["cost"], 0.30, places=6)

    def test_a_nan_cost_in_the_ledger_is_repriced_rather_than_poisoning_the_total(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(json.dumps({"ts": "2026-09-22T09:00:00Z", "prompt_tokens": 4_203_926,
                                           "completion_tokens": 51_649, "cost_usd": "nan"}) + "\n",
                               encoding="utf-8")
        self.assertAlmostEqual(mb.spend_today(self.ledger, "2026-09-22")["cost"], 0.129305, places=5)

    def test_a_line_without_a_cost_is_priced_from_its_tokens(self):
        """A hand-written or older line must still count, or the total silently understates."""
        self.spend(0.0, "2026-09-22")
        path = self.ledger
        path.write_text(json.dumps({"ts": "2026-09-22T10:00:00Z", "prompt_tokens": 4_203_926,
                                    "completion_tokens": 51_649}) + "\n", encoding="utf-8")
        self.assertAlmostEqual(mb.spend_today(path, "2026-09-22")["cost"], 0.129305, places=5)

    def test_a_corrupt_ledger_line_is_skipped_not_fatal(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text('{"ts": "2026-09-22T09:00:00Z", "cost_usd": 0.5}\n'
                               'not json at all\n\n[]\n', encoding="utf-8")
        self.assertAlmostEqual(mb.spend_today(self.ledger, "2026-09-22")["cost"], 0.5, places=6)

    def test_a_ledger_line_with_no_timestamp_is_counted_as_degraded_not_as_spend(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(json.dumps({"cost_usd": 9.99}) + "\n", encoding="utf-8")
        today = mb.spend_today(self.ledger, "2026-09-22")
        self.assertEqual(today["cost"], 0.0)
        self.assertEqual(today["unreadable"], 1)


# ------------------------------------------------------------------ the dial and its degrade paths
class TestTheDial(Scratch):
    def test_the_workspace_dial_is_the_one_the_gate_uses(self):
        self.dial({"budget": {"daily_usd": 0.5, "on_exceed": "stop", "throttle_rate": 0.5}})
        dial = mb.load_budget(self.ws)
        self.assertEqual(dial["daily_usd"], 0.5)
        self.assertEqual(dial["on_exceed"], "stop")
        self.assertTrue(dial["explicit"])

    def test_the_tenant_config_is_read_when_the_workspace_has_no_dial(self):
        dial = mb.load_budget(self.ws, {"budget": {"daily_usd": 2.5, "on_exceed": "warn"}})
        self.assertEqual(dial["daily_usd"], 2.5)
        self.assertEqual(dial["source"], "the tenant config")

    def test_a_missing_dial_degrades_to_the_default_and_says_so(self):
        dial = mb.load_budget(self.ws)
        self.assertFalse(dial["explicit"])
        self.assertEqual(dial["daily_usd"], mb.DEFAULT_DAILY_USD)
        self.assertTrue(dial["degraded"], "a missing dial must be reported, never assumed")
        self.assertIn("no budget block", dial["degraded"][0])

    def test_an_unparsable_value_degrades_to_the_default_and_names_the_value(self):
        self.dial({"budget": {"daily_usd": "lots", "on_exceed": "explode", "throttle_rate": 7}})
        dial = mb.load_budget(self.ws)
        self.assertEqual(dial["daily_usd"], mb.DEFAULT_DAILY_USD)
        self.assertEqual(dial["on_exceed"], mb.DEFAULT_ON_EXCEED)
        self.assertEqual(dial["throttle_rate"], mb.DEFAULT_THROTTLE_RATE)
        joined = " ".join(dial["degraded"])
        for named in ("lots", "explode", "7"):
            self.assertIn(named, joined, f"the refusal must name the value it refused ({named})")

    def test_a_truncated_json_dial_is_not_fatal(self):
        (self.ws / "config.json").write_text('{"budget": {"daily_usd": 0.5', encoding="utf-8")
        dial = mb.load_budget(self.ws)
        self.assertEqual(dial["daily_usd"], mb.DEFAULT_DAILY_USD)
        self.assertTrue(any("not valid JSON" in note for note in dial["degraded"]))

    def test_a_negative_or_absurd_budget_is_refused_not_obeyed(self):
        for bad in (0, -3, 10 ** 9, "0", "nan", "inf"):
            with self.subTest(daily_usd=bad):
                self.dial({"budget": {"daily_usd": bad, "on_exceed": "stop"}})
                dial = mb.load_budget(self.ws)
                self.assertEqual(dial["daily_usd"], mb.DEFAULT_DAILY_USD)

    def test_a_budget_block_that_is_not_a_block_is_reported(self):
        self.dial({"budget": "cheap"})
        dial = mb.load_budget(self.ws)
        self.assertEqual(dial["daily_usd"], mb.DEFAULT_DAILY_USD)
        self.assertTrue(any("must be a block" in note for note in dial["degraded"]))

    def test_the_dial_is_carried_into_the_file_the_runtime_reads(self):
        """The source of truth is the tenant config; an unattended sweep can only read the workspace."""
        path = mb.write_budget(self.ws, daily_usd=0.75, on_exceed="throttle", throttle_rate=0.5)
        self.assertEqual(path, self.ws / "config.json")
        dial = mb.load_budget(self.ws)
        self.assertEqual((dial["daily_usd"], dial["on_exceed"], dial["throttle_rate"]),
                         (0.75, "throttle", 0.5))

    def test_a_change_updates_the_file_that_already_speaks_rather_than_a_second_one(self):
        self.dial({"channels": ["telegram"], "budget": {"daily_usd": 1.0}}, name="notify.json")
        path = mb.write_budget(self.ws, daily_usd=2.0)
        self.assertEqual(path, self.ws / "notify.json", "the file that already carries a budget wins")
        self.assertFalse((self.ws / "config.json").exists(), "no second dial file may appear")
        data = json.loads((self.ws / "notify.json").read_text(encoding="utf-8"))
        self.assertEqual(data["channels"], ["telegram"], "the carry must merge, never clobber")
        self.assertEqual(data["budget"]["daily_usd"], 2.0)


# ------------------------------------------------------------------ ask: the sweep's own question
class TestAskTheSweep(Scratch):
    def test_within_budget_the_full_cap_comes_back(self):
        self.dial({"budget": {"daily_usd": 1.0, "on_exceed": "throttle"}})
        code, out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "10")
        self.assertEqual(code, 0)
        self.assertEqual(out, "10")
        self.assertEqual(err, "")

    def test_a_spent_budget_returns_a_reduced_number_and_says_why(self):
        self.dial({"budget": {"daily_usd": 0.10, "on_exceed": "throttle", "throttle_rate": 0.25}})
        self.spend(0.30)
        code, out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "10")
        self.assertEqual(code, 72, "72 is a decision, not an error")
        self.assertEqual(int(out), 2)
        self.assertIn("$0.30", err)       # the sentence states the spend, the budget and the rate
        self.assertIn("25%", err)

    def test_stop_says_do_not_run_and_returns_zero_volume(self):
        self.dial({"budget": {"daily_usd": 0.10, "on_exceed": "stop"}})
        self.spend(0.30)
        code, out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "10")
        self.assertEqual(code, 70)
        self.assertEqual(int(out), 0)
        self.assertIn("does not run", err)
        self.assertIn("Settings", err)

    def test_warn_reports_the_overrun_and_throttles_nothing(self):
        self.dial({"budget": {"daily_usd": 0.10, "on_exceed": "warn"}})
        self.spend(0.30)
        code, out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "10")
        self.assertEqual(code, 0)
        self.assertEqual(out, "10")
        self.assertIn("Nothing is throttled", err)

    def test_a_broken_dial_never_stops_or_slows_a_paying_hunt(self):
        """The whole point of the degrade rule: something is wrong with a FILE, not with the account."""
        self.dial({"budget": {"daily_usd": "NaN", "on_exceed": "stop", "throttle_rate": "half"}})
        self.spend(99.0)
        code, out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "10")
        self.assertEqual(code, 0, "a degraded dial must not stop a run")
        self.assertEqual(out, "10", "a degraded dial must not cut the volume either")
        self.assertIn("degraded", err)

    def test_a_missing_ledger_is_zero_spend_not_an_error(self):
        self.dial({"budget": {"daily_usd": 1.0, "on_exceed": "throttle"}})
        code, out, _ = cli("ask", "--workspace", str(self.ws), "--plan-cap", "4")
        self.assertEqual((code, out), (0, "4"))

    def test_a_sweep_that_would_cross_the_budget_is_flagged_before_it_spends(self):
        self.dial({"budget": {"daily_usd": 1.0, "on_exceed": "warn"}})
        self.spend(0.85)
        code, _out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "4")
        self.assertEqual(code, 0)
        self.assertIn("one more sweep", err)

    def test_nothing_over_budget_says_nothing(self):
        self.dial({"budget": {"daily_usd": 1.0, "on_exceed": "throttle"}})
        self.spend(0.05)
        _code, _out, err = cli("ask", "--workspace", str(self.ws), "--plan-cap", "4")
        self.assertEqual(err, "", "an ordinary run must stay silent")

    def test_status_reports_today_against_the_dial_in_json(self):
        self.dial({"budget": {"daily_usd": 2.0, "on_exceed": "throttle"}})
        self.spend(0.5)
        code, out, _ = cli("status", "--workspace", str(self.ws), "--json")
        self.assertEqual(code, 0)
        body = json.loads(out)
        self.assertEqual(body["budget"]["daily_usd"], 2.0)
        self.assertAlmostEqual(body["spent_today_usd"], 0.5, places=4)
        self.assertAlmostEqual(body["remaining_usd"], 1.5, places=4)
        self.assertEqual(body["action"], "ok")
        self.assertEqual(body["ledger"], str(self.ws / "data" / "usage.jsonl"))


# ------------------------------------------------------------------ record: where the numbers come from
class TestRecordMeasuresFromTheAudit(Scratch):
    def audit(self, lines):
        path = self.tmp / "usage_audit.jsonl"
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        return path

    def test_the_runs_measured_usage_comes_from_the_engines_audit(self):
        audit = self.audit([
            {"ts": "2026-09-22T09:00:00Z", "job_name": "jane-doe-job-hunt", "prompt_tokens": 4_100_000,
             "completion_tokens": 50_000, "model": "deepseek-v4-flash"},
            {"ts": "2026-09-22T09:40:00Z", "job_name": "jane-doe-job-hunt", "prompt_tokens": 103_926,
             "completion_tokens": 1_649, "model": "deepseek-v4-flash"},
            {"ts": "2026-09-22T09:10:00Z", "job_name": "jane-doe-mail", "prompt_tokens": 1_100_000,
             "completion_tokens": 19_000},
        ])
        code, out, _err = cli("record", "--workspace", str(self.ws), "--audit", str(audit),
                              "--job", "job-hunt", "--run-id", "live-1")
        self.assertEqual(code, 0, out)
        line = json.loads(self.ledger.read_text(encoding="utf-8").strip())
        self.assertEqual(line["prompt_tokens"], 4_203_926)
        self.assertEqual(line["completion_tokens"], 51_649)
        self.assertEqual(line["runs"], 2)
        self.assertEqual(line["model"], "deepseek-v4-flash")
        self.assertEqual(line["job"], "job-hunt")
        self.assertAlmostEqual(line["cost_usd"], 0.129305, places=5)
        self.assertIn("$0.1293", out)

    def test_only_runs_after_the_start_time_are_counted(self):
        audit = self.audit([
            {"ts": "2026-09-22T08:00:00Z", "job_name": "job-hunt", "prompt_tokens": 4_000_000,
             "completion_tokens": 50_000},
            {"ts": "2026-09-22T09:30:00Z", "job_name": "job-hunt", "prompt_tokens": 4_203_926,
             "completion_tokens": 51_649},
        ])
        cli("record", "--workspace", str(self.ws), "--audit", str(audit), "--job", "job-hunt",
            "--since", "2026-09-22T09:00:00Z", "--run-id", "live-2")
        line = json.loads(self.ledger.read_text(encoding="utf-8").strip())
        self.assertEqual(line["prompt_tokens"], 4_203_926, "an earlier run belongs to an earlier day")

    def test_a_failed_run_is_not_billed_into_the_ledger(self):
        audit = self.audit([{"ts": "2026-09-22T09:30:00Z", "job_name": "job-hunt", "error": "boom",
                             "prompt_tokens": 4_000_000, "completion_tokens": 1}])
        code, _out, err = cli("record", "--workspace", str(self.ws), "--audit", str(audit),
                              "--job", "job-hunt", "--run-id", "x")
        self.assertEqual(code, 3)
        self.assertIn("no usage audit line matched", err)
        self.assertFalse(self.ledger.exists(), "nothing measured must write nothing, never a $0.00 line")

    def test_an_unmeasurable_run_is_refused_loudly_and_writes_nothing(self):
        code, _out, err = cli("record", "--workspace", str(self.ws), "--audit",
                              str(self.tmp / "does-not-exist.jsonl"), "--run-id", "x")
        self.assertEqual(code, 3)
        self.assertIn("nothing was written", err)
        self.assertFalse(self.ledger.exists())

    def test_a_known_figure_can_be_recorded_without_an_audit(self):
        code, out, _ = cli("record", "--workspace", str(self.ws), "--tokens-in", "4203926",
                           "--tokens-out", "51649", "--model", "deepseek-v4-flash")
        self.assertEqual(code, 0)
        self.assertIn("$0.1293", out)
        line = json.loads(self.ledger.read_text(encoding="utf-8").strip())
        self.assertEqual(line["source"], "given on the command line")


# ------------------------------------------------------------------ no surface hides the spend
class TestBothSidesCanSeeTheSpend(unittest.TestCase):
    """The subscriber pays for the spend and the operator carries it, so both must be able to read it.

    The dial is only worth having if it is visible where the decisions are made: the Alerts view (why
    this sweep did less), the Cost panel (what today cost), and Settings (the dial itself, writable).
    """

    def test_the_api_carries_the_budget_state_beside_the_backoff(self):
        srv = SERVER.read_text(encoding="utf-8")
        self.assertIn('"budget": budget', srv, "the alerts payload must carry the budget state")
        self.assertIn("import model_budget", srv)
        self.assertIn("budget_state_for(project, cfg)", srv)

    def test_settings_can_read_and_change_the_dial(self):
        srv = SERVER.read_text(encoding="utf-8")
        self.assertIn('"budget": {"current": view.get("budget")', srv,
                      "the dials route must expose the budget to the interface")
        self.assertIn("budget.daily_usd", srv)
        self.assertIn("budget.on_exceed", srv)
        m = re.search(r'"writable":\s*\[([^\]]*)\]', srv)
        self.assertIn("budget", m.group(1), "the page's account of what can change must stay true")
        self.assertIn("_set_in_block", srv, "the dial needs a writer anchored on its own block")

    def test_the_alerts_view_renders_the_sentence_the_cost_panel_the_figure(self):
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("a.budget && a.budget.line", js, "the Alerts view must say why a sweep did less")
        self.assertIn("a.budget.spent_today_usd", js)
        self.assertIn("spent today", js, "the Cost panel must show today's spend")
        self.assertIn("u.budget", js)

    def test_settings_offers_the_dial_and_saves_it(self):
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn('id="c-budget"', js)
        self.assertIn('id="c-on-exceed"', js)
        self.assertIn("budget: {daily_usd:", js, "the save payload must carry the dial")

    def test_the_usage_route_reports_which_source_it_counted(self):
        srv = SERVER.read_text(encoding="utf-8")
        self.assertIn("this account's own ledger", srv)
        self.assertIn('"budget": budget_state_for(ws, cfg)', srv)

    def test_the_template_ships_the_dial_documented(self):
        text = CONFIG.read_text(encoding="utf-8")
        self.assertIn("budget:", text)
        block = text[text.index("\nbudget:"):][:400]
        self.assertIn("daily_usd:", block)
        self.assertIn("on_exceed:", block)
        self.assertIn("throttle_rate:", block)
        for action in mb.EXCEED_ACTIONS:
            self.assertIn(action, block, "the template must document every value the gate accepts")

    def test_the_gate_ships_to_new_accounts_with_its_dial(self):
        prov = (ROOT / "provisioning" / "provision_tenant.py").read_text(encoding="utf-8")
        self.assertIn("model_budget.py", prov, "a new account would not get the gate")
        self.assertIn("carry_budget_dial", prov,
                      "a new account whose dial never travelled has no budget at all")

    def test_the_ledger_path_has_one_definition_the_operator_can_read(self):
        import importlib.util as _u

        s = _u.spec_from_file_location("jha_tc_probe", ROOT / "engine" / "scripts" / "tenant_config.py")
        tc = _u.module_from_spec(s)
        s.loader.exec_module(tc)
        ws = pathlib.Path("/tmp/example-workspace")
        self.assertEqual(tc.usage_ledger({}, ws), mb.ledger_path(ws))
        self.assertEqual(tc.usage_ledger({"ops": {"usage_ledger": "/tmp/x.jsonl"}}, ws),
                         pathlib.Path("/tmp/x.jsonl"))


# ------------------------------------------------------------------ the two surfaces an account is judged by
class TestTheDashboardsSpendIsTheLedgersSpend(Scratch):
    """The Cost panel must show the number the budget gate enforced, not a second total.

    Found by running it: an aggregated ledger line (the install's backfill carries runs=35) counted as ONE
    run, so the panel that the plan allowance is measured against under-reported 35 runs as 1.
    """

    def test_the_cost_panel_counts_the_runs_a_ledger_line_aggregates(self):
        cfg = self.tmp / "tenant.yaml"
        cfg.write_text(f"tenant:\n  slug: jane-doe\nbilling:\n  plan: starter\n"
                       f"paths:\n  workspace: \"{self.ws}\"\n", encoding="utf-8")
        day = mb.spend_today(None, "")["day"]
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(json.dumps({"ts": f"{day}T22:45:36Z", "slug": "jane-doe", "runs": 35,
                                           "prompt_tokens": 88_857_294, "completion_tokens": 758_267,
                                           "cost_usd": 2.667725}) + "\n", encoding="utf-8")
        dash = spec("jha_dash_probe", SERVER)
        (self.tmp / "usage").mkdir()
        dash.USAGE_DIR = self.tmp / "usage"
        original = dash.workspace_for
        dash.workspace_for = lambda cfg: self.ws
        try:
            usage = dash.usage_for("jane-doe", plan="starter", cfg_path=cfg)
        finally:
            dash.workspace_for = original
        self.assertEqual(usage["measurement_source"], "this account's own ledger")
        self.assertEqual(usage["runs"], 35, "the plan allowance is measured in runs, not in ledger lines")
        self.assertAlmostEqual(usage["spend"], 2.6677, places=3)
        self.assertIsNotNone(usage["budget"], "the same payload carries the dial and today's figure")
        self.assertAlmostEqual(usage["budget"]["spent_today_usd"], 2.6677, places=3)

    def test_an_empty_ledger_falls_back_to_the_older_meter(self):
        """A managed deployment's meter still counts when the account has no ledger yet."""
        cfg = self.tmp / "tenant.yaml"
        cfg.write_text(f"tenant:\n  slug: jane-doe\npaths:\n  workspace: \"{self.ws}\"\n",
                       encoding="utf-8")
        meter = self.tmp / "usage"
        meter.mkdir()
        day = mb.spend_today(None, "")["day"]
        (meter / "jane-doe.jsonl").write_text(json.dumps({"ts": f"{day}T09:00:00Z", "runs": 4,
                                                          "prompt_tokens": 4_203_926,
                                                          "completion_tokens": 51_649}) + "\n",
                                              encoding="utf-8")
        dash = spec("jha_dash_probe2", SERVER)
        dash.USAGE_DIR = meter
        original = dash.workspace_for
        dash.workspace_for = lambda cfg: self.ws
        try:
            usage = dash.usage_for("jane-doe", plan="starter", cfg_path=cfg)
        finally:
            dash.workspace_for = original
        self.assertEqual(usage["runs"], 4)
        self.assertEqual(usage["measurement_source"], "the product meter")


class TestTheOperatorSeesTheLedger(unittest.TestCase):
    """The operator's own CLI has to read the account's ledger, or the only per-account figure in the
    product is the one in the dashboard, which is not where a margin is watched."""

    def test_cost_report_reads_each_tenants_own_ledger(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="jha-cost-"))
        (tmp / "tools").mkdir()
        for name in ("cost_report.py", "price_model.py"):
            shutil.copy(ROOT / "tools" / name, tmp / "tools" / name)
        shutil.copy(ROOT / "pricing.yaml", tmp / "pricing.yaml")
        ws = tmp / "hunts" / "jane-doe"
        (ws / "data").mkdir(parents=True)
        day = time.strftime("%Y-%m-%d", time.gmtime())
        (ws / "data" / "usage.jsonl").write_text(json.dumps({
            "ts": f"{day}T09:00:00Z", "runs": 35, "prompt_tokens": 88_857_294,
            "completion_tokens": 758_267, "cost_usd": 2.667725}) + "\n", encoding="utf-8")
        (tmp / "config").mkdir()
        (tmp / "config" / "tenant.yaml").write_text(
            f'tenant:\n  slug: jane-doe\nbilling:\n  plan: starter\npaths:\n  workspace: "{ws}"\n',
            encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "tools" / "cost_report.py"), "--json"],
                           capture_output=True, text=True, cwd=str(tmp))
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        body = json.loads(r.stdout)
        self.assertEqual(body["jane-doe"]["runs"], 35)
        self.assertAlmostEqual(body["jane-doe"]["cost"], 2.6677, places=3)


# ------------------------------------------------------------------ the prompt asks, or nothing happens
class TestTheLiveSweepConsultsTheBudget(unittest.TestCase):
    """A gate nothing asks for enforces nothing. The volume decision lives in the prompt.

    Same shape as tests/test_prompt_drift_backoff.py: read the live stores and refuse a sweep prompt that
    never asks. The failure it guards is silent - applications keep going out at full volume and the
    budget is decorative.
    """

    MARKER = "MODEL BUDGET"

    def live_prompts(self):
        found = []
        for jobs_file in sorted(PROFILES.glob("*/cron/jobs.json")):
            try:
                d = json.loads(jobs_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for j in (d if isinstance(d, list) else d.get("jobs", [])):
                if (j.get("name") or "").endswith("job-hunt"):
                    found.append((j.get("name"), j.get("prompt") or j.get("command") or ""))
        return found

    def test_the_template_asks_before_it_spends(self):
        jobs = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        sweep = [j for j in (jobs if isinstance(jobs, list) else jobs["jobs"])
                 if (j.get("name") or "").endswith("job-hunt")]
        self.assertEqual(len(sweep), 1)
        prompt = sweep[0]["prompt"]
        self.assertIn(self.MARKER, prompt)
        for needle in ("model_budget.py ask --plan-cap", "model_budget.py line",
                       "model_budget.py record --job", "STATE that sentence"):
            self.assertIn(needle, prompt, f"the template prompt must name {needle}")

    def test_each_live_sweep_prompt_asks_for_the_cap_and_records_the_cost(self):
        found = self.live_prompts()
        if not found:
            self.skipTest("no live sweep jobs on this host")
        for name, text in found:
            with self.subTest(job=name):
                self.assertIn(self.MARKER, text)
                self.assertIn("model_budget.py ask --plan-cap", text)
                self.assertIn("model_budget.py line", text)
                self.assertIn("model_budget.py record", text)


if __name__ == "__main__":
    unittest.main()
