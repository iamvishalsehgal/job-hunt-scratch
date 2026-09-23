#!/usr/bin/env python3
"""The template stores schedules as STRINGS (\"every 360m\", \"0 4 * * 0\"); provisioning renders them. My first
pass wrote dicts, which broke the template tests. This restores the string shape and moves the remaining
model-using template jobs out of peak hours (DeepSeek peak: 01:00-04:00, 06:00-10:00 UTC Mon-Fri).

Usage: fix_template_schedules.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
TPL = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json")
# name suffix -> (string schedule, why)
AS_STRING = {
    "{{SLUG}}-job-hunt": "*/10 0,4,5,10-23 * * *",
    "{{SLUG}}-mail": "*/5 0,4,5,10-23 * * *",
    "{{SLUG}}-otp-watch": "*/5 0,4,5,10-23 * * *",
    "{{SLUG}}-error-triage": "0 11 * * *",          # was 0 6 (peak)
    "{{SLUG}}-agency-watch": "30 11 * * *",         # was 30 8 (peak)
    "{{SLUG}}-google-api-watchdog": "0 12 * * *",   # was 0 7 (peak)
}


def main() -> int:
    apply = "--apply" in sys.argv
    data = json.loads(TPL.read_text(encoding="utf-8"))
    for job in data:
        want = AS_STRING.get(job["name"])
        if not want:
            continue
        if job.get("no_agent") and job["name"].endswith("google-api-watchdog"):
            want = "0 12 * * *"      # a script job: no token cost, but keep it out of peak anyway
        current = job.get("schedule")
        if current == want:
            print("   %-30s already %s" % (job["name"], want))
            continue
        print("   %-30s %r -> %r (agent=%s)" % (job["name"], current, want, not job.get("no_agent")))
        job["schedule"] = want
    if apply:
        shutil.copy2(TPL, TPL.with_name(TPL.name + ".bak-schedfix-" + STAMP))
        tmp = TPL.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(TPL)
        print("   template written")
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
