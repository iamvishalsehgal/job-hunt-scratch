#!/usr/bin/env python3
"""Owner rule 23 Sep 2026: off-peak sweeps, clean drafts, and the writing rules that keep them clean.

1. THE SWEEPS RUN ONLY IN DEEPSEEK'S OFF-PEAK WINDOW. Official pricing: peak is 01:00-04:00 and 06:00-10:00
   UTC, Monday-Friday; every other hour is off-peak at half price. Schedule becomes `*/10 0,4,5,10-23 * * *`
   - every off-peak hour, none of the peak ones.
2. The two drafts already on disk are scrubbed with the TOOL'S OWN stripper, so on-disk and send-time agree.
   (One of them, Momo Medical, was already sent WITH the annotation; that mail cannot be recalled.)
3. Both prompts gain the draft-shape rule and the bot-vocabulary rule.

Usage: offpeak_and_hygiene.py [--apply]
"""
import importlib.util
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
OFFPEAK_EXPR = "*/10 0,4,5,10-23 * * *"
NEWLINE = chr(10)

RULE = '''
### THE DRAFT IS A WORKING FILE, THE SENT MAIL IS ONLY THE LETTER (owner rule, 23 Sep 2026)

`applications/<slug>/email-to-hr.md` is read by the tool and by you; the employer sees only what survives.
Write it so its FIRST LINE is the greeting, with the tool's own meta lines above it:

    To: <address>            <- meta, dropped by the tool
    Subject: ...             <- meta, parsed by the tool
    Wants: ...               <- meta, dropped by the tool

    Dear <Company> recruiting team,

    ... the letter, formatted, paragraphs separated by blank lines ...

Never put any of these in the body, in any form:
- a markdown heading (`# email to HR - <company>, <role>`) - the pack folder already names the role;
- a line explaining the guard, the evidence, the exit code or the route (`Recipient evidence: ...`,
  `email_guard exit 20 SEND_GENERIC`, `route: email_named`, `source: colophon`);
- a line naming the tracker, the ledger, the engine, the sweep or a `tools/...` path.
The tool drops annotation lines and REFUSES the send when a tooling word survives inside a sentence, so writing
them costs a retry. The employer must never be able to tell that a machine prepared the mail.

NEVER write machine or assistant vocabulary anywhere in a draft or a letter: no 'as an AI', no 'language
model', no 'the bot' or 'the job-hunt bot', no 'this tool sent', no 'automated message', no 'do not reply'.
The scrubber removes such sentences, which silently shortens the letter - write as the candidate, plainly.
'''


def load_apply_email():
    spec = importlib.util.spec_from_file_location(
        "ae_hygiene", "/home/ubuntu/jobhunt-agent/engine/notify/apply_email.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def patch_prompt(prompt: str):
    if "THE DRAFT IS A WORKING FILE" in prompt:
        return prompt, False
    anchor = "### THE EMAIL IS FORMATTED, NEVER ONE PARAGRAPH"
    if anchor not in prompt:
        return prompt, False
    i = prompt.index(anchor)
    j = prompt.find(NEWLINE + "## ", i)
    insert_at = j if j > 0 else len(prompt)
    return prompt[:insert_at] + NEWLINE + RULE + prompt[insert_at:], True


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")

    print("1. schedules -> off-peak only")
    for slug in ("vishal", "nhung"):
        path = pathlib.Path("/home/ubuntu/.hermes/profiles/%s/cron/jobs.json" % slug)
        data = json.loads(path.read_text(encoding="utf-8"))
        job = [j for j in data["jobs"] if j["name"].endswith("job-hunt")][0]
        print("   %s: %s -> %s" % (slug, job["schedule_display"], OFFPEAK_EXPR))
        if apply:
            shutil.copy2(path, path.with_name(path.name + ".bak-offpeak-" + STAMP))
            job["schedule"] = {"kind": "cron", "expr": OFFPEAK_EXPR, "display": OFFPEAK_EXPR}
            job["schedule_display"] = OFFPEAK_EXPR
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + NEWLINE, encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)

    print("2. scrub the drafts already on disk (tool's own stripper)")
    ae = load_apply_email()
    for slug, pack in (("vishal", "tennet-data-engineer-market-analysis"),
                       ("vishal", "momo-medical-backend-developer-integrations-team")):
        p = pathlib.Path("/home/ubuntu/.hermes/profiles/%s/workspace/applications/%s/email-to-hr.md"
                         % (slug, pack))
        if not p.is_file():
            print("   %s: no draft" % pack)
            continue
        before = p.read_text(encoding="utf-8")
        clean, notes = ae.strip_internal_notes(before)
        clean = clean.strip() + NEWLINE
        leak = ae.internal_leak_problem(clean)
        print("   %s: %d -> %d chars, dropped %d line(s), leak=%s"
              % (pack, len(before), len(clean), len(notes), leak or "none"))
        for n in notes:
            print("      - %s" % n[:90])
        if apply and clean != before:
            shutil.copy2(p, p.with_name(p.name + ".bak-annot-" + STAMP))
            p.write_text(clean, encoding="utf-8")

    print("3. prompts: the draft-shape rule")
    targets = [("template", pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json"),
                "{{SLUG}}-job-hunt")]
    for slug in ("vishal", "nhung"):
        targets.append((slug, pathlib.Path("/home/ubuntu/.hermes/profiles/%s/cron/jobs.json" % slug),
                        "%s-job-hunt" % slug))
    for label, path, jobname in targets:
        data = json.loads(path.read_text(encoding="utf-8"))
        jobs = data if isinstance(data, list) else data["jobs"]
        job = [j for j in jobs if j["name"] == jobname][0]
        new, changed = patch_prompt(job["prompt"])
        print("   %s: %d -> %d chars, changed=%s" % (label, len(job["prompt"]), len(new), changed))
        if apply and changed:
            shutil.copy2(path, path.with_name(path.name + ".bak-draftshape-" + STAMP))
            job["prompt"] = new
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + NEWLINE, encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
