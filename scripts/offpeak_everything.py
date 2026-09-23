#!/usr/bin/env python3
"""Put every MODEL-USING job in the off-peak window, live profiles and the tenant template alike.

Owner rule 23 Sep 2026: the whole bot runs off-peak (DeepSeek peak is 01:00-04:00 and 06:00-10:00 UTC
Mon-Fri; every other hour is half price). Script-only jobs (no_agent) cost nothing and keep their cadence, so
they are left alone.

The live mail job moves to every 5 minutes inside the window rather than its 10-minute round-the-clock
cadence: worst case an invite that arrives just as peak opens waits until the window reopens, which the run
summary states plainly.

Usage: offpeak_everything.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
NEWLINE = chr(10)
WINDOW = "0,4,5,10-23"
SWEEP_EXPR = "*/10 %s * * *" % WINDOW
MAIL_EXPR = "*/5 %s * * *" % WINDOW


def is_offpeak_expr(job) -> bool:
    sched = job.get("schedule") or {}
    expr = sched.get("expr") if isinstance(sched, dict) else ""
    return isinstance(expr, str) and WINDOW in expr


def set_expr(path, jobname, expr, apply, label):
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data if isinstance(data, list) else data["jobs"]
    job = [j for j in jobs if j["name"] == jobname or j["name"].endswith(jobname)]
    if not job:
        print("   %-34s no such job" % label)
        return
    job = job[0]
    if is_offpeak_expr(job):
        print("   %-34s already off-peak" % label)
        return
    print("   %-34s %s -> %s" % (label, job.get("schedule_display"), expr))
    if apply:
        shutil.copy2(path, path.with_name(path.name + ".bak-offpeak2-" + STAMP))
        job["schedule"] = {"kind": "cron", "expr": expr, "display": expr}
        job["schedule_display"] = expr
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + NEWLINE, encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(path)


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")

    print("live mail jobs -> off-peak, every 5m in the window")
    for slug in ("vishal", "nhung"):
        set_expr(pathlib.Path("/home/ubuntu/.hermes/profiles/%s/cron/jobs.json" % slug),
                 "-mail", MAIL_EXPR, apply, "%s-mail" % slug)

    print("tenant template: every model-using job -> off-peak")
    tpl = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json")
    data = json.loads(tpl.read_text(encoding="utf-8"))
    for job in data:
        if job.get("no_agent"):
            continue
        current = job.get("schedule")
        printed = current.get("display") if isinstance(current, dict) else current
        if is_offpeak_expr(job):
            print("   %-34s already off-peak" % job["name"])
            continue
        if not job["name"].endswith(("-job-hunt", "-mail", "-otp-watch")):
            # Weekly/occasional jobs (repo-improve runs Sun 05:00, which is off-peak anyway) keep their
            # cadence: shifting them onto an every-10-minute expression would change what they DO.
            print("   %-34s left alone (%s; not a cadence this rule governs)" % (job["name"], printed))
            continue
        expr = MAIL_EXPR if job["name"].endswith(("-mail", "-otp-watch")) else SWEEP_EXPR
        print("   %-34s %s -> %s" % (job["name"], printed, expr))
        if apply:
            job["schedule"] = {"kind": "cron", "expr": expr, "display": expr}
    if apply:
        shutil.copy2(tpl, tpl.with_name(tpl.name + ".bak-offpeak2-" + STAMP))
        tmp = tpl.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + NEWLINE, encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(tpl)
        print("   template written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
