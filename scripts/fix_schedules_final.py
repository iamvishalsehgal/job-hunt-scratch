#!/usr/bin/env python3
"""Final scheduling pass, correcting the two mistakes of the previous one.

1. SCRIPT-ONLY jobs were moved for no reason: error-triage, google-api-watchdog and agency-watch are no_agent
   jobs, so they spend no model tokens and must keep their original times (a template test pins them).
2. otp-watch goes back to `every 5m`. It reads portal verification codes, which expire in minutes: a code
   requested at 05:55 by a sweep still running at 06:05 must be read, not waited on until the window reopens.
   It only spends anything when a code is actually in the mailbox, so keeping it available costs ~nothing.
3. The CADENCE IS DECLARED IN THE TENANT CONFIG, and a test asserts the config and the template agree - so
   both tenant configs get the off-peak values too.

Usage: fix_schedules_final.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
TPL = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json")
RESTORE = {
    "{{SLUG}}-otp-watch": "every 5m",
    "{{SLUG}}-error-triage": "0 6 * * *",
    "{{SLUG}}-google-api-watchdog": "0 7 * * *",
    "{{SLUG}}-agency-watch": "30 8 * * *",
}
KEEP = {
    "{{SLUG}}-job-hunt": "*/10 0,4,5,10-23 * * *",
    "{{SLUG}}-mail": "*/5 0,4,5,10-23 * * *",
}
CONFIG_EDITS = {
    "/home/ubuntu/jobhunt-agent/config/tenant.example.yaml": {
        'sweep: "every 180m"': 'sweep: "*/10 0,4,5,10-23 * * *"',
        'mailbox: "every 20m"': 'mailbox: "*/5 0,4,5,10-23 * * *"',
    },
    "/home/ubuntu/jobhunt-agent/config/tenant.yaml": {
        'sweep: "every 180m"': 'sweep: "*/10 0,4,5,10-23 * * *"',
        'mailbox: "every 20m"': 'mailbox: "*/5 0,4,5,10-23 * * *"',
    },
}


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")
    data = json.loads(TPL.read_text(encoding="utf-8"))
    changed = False
    for job in data:
        want = RESTORE.get(job["name"]) or KEEP.get(job["name"])
        if not want or job.get("schedule") == want:
            continue
        print("   %-30s %r -> %r" % (job["name"], job.get("schedule"), want))
        job["schedule"] = want
        changed = True
    if apply and changed:
        shutil.copy2(TPL, TPL.with_name(TPL.name + ".bak-schedfinal-" + STAMP))
        tmp = TPL.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(TPL)
        print("   template written")
    for path, edits in CONFIG_EDITS.items():
        p = pathlib.Path(path)
        text = p.read_text(encoding="utf-8")
        for old, new in edits.items():
            if old in text:
                print("   %s: %s -> %s" % (p.name, old, new))
                text = text.replace(old, new)
        if apply:
            shutil.copy2(p, p.with_name(p.name + ".bak-schedfinal-" + STAMP))
            p.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
