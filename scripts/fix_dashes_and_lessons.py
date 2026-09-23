#!/usr/bin/env python3
"""Two fixes after syncing the hotfixes into the template.

1. The repo's own rule (tests/test_ship_clean.py) forbids an em/en dash in any tracked file, and
   jobs.template.json carried two literal ones from the ported text. Reworded: the rule now names the
   code points instead of the glyph, which keeps the meaning and satisfies the checker.
2. The incident lessons were appended INLINE to the prompt; the playbook checker requires a moved section
   to be pointer-only. The body moves into engine/references/lessons.md - where the prompt's own LESSONS
   pointer already sends the agent - and the prompts keep just the pointer.

Usage: fix_dashes_and_lessons.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
EM, EN = "\u2014", "\u2013"
LESSONS_MARK = "## LESSONS FROM THE 22-23 SEP INCIDENTS"

DASH_FIXES = [
    (f"NEVER use the em-dash character ({EM}) in ANY application material",
     "NEVER use the em-dash (U+2014) or en-dash (U+2013) in ANY application material",
     "strict-format rule"),
    (f"years-of-experience requirements {EM} apply regardless",
     "years-of-experience requirements: apply regardless",
     "years-of-experience line"),
]

LESSON_BODY = """
## Incidents (22-23 Sep 2026) - each one cost a real sweep

1. **A code-guard refusal is a TO-DO, not a verdict.** A 169-word body (cap 150) and a quoted EUR 60,000
   (standing quote EUR 4,400-5,000) parked four winnable roles as Blocked. Cut the body, drop the figure,
   render the missing files, run the same command again - at most twice.
2. **A pack holding only `jd.md` is unfinished, never a Blocked role.** Write `tailoring.json` and render
   `cv.pdf` + `cover-letter.pdf` for THAT role first; the tool's refusal is the instruction to build it.
3. **Before deploying a ported prompt, verify every file and command it names exists for THIS candidate.**
   A port carried an account-gating helper into a workspace where the file did not exist. Test the paths.
4. **After a prompt swap, grep for every hotfix added since the previous version, not just the headings.**
   A port silently moved a CRON-SAFE section from `##` to `###` and a heading check called it present.
5. **A throttle driven by a row STATUS must read the row's notes and release once the event is past.** Four
   rows in Interview state (two finished) held the pipeline at 40% for ten days; a contract end date in the
   same note read as a live interview until that date.
6. **When you add a kind or a route, update EVERY map that enumerates them** (status maps, help strings,
   the check report, docs) - a new `reply` kind crashed the mail command with `KeyError` on first use.
7. **A behaviour change that contradicts an earlier hard rule ships behind a per-candidate dial.** Replies
   to employers were forbidden outright; the dial turns them on for one account only, default stays refused.
8. **Measure a run's real duration before raising its cadence.** The fire-claim TTL is 300 s and a missed
   slot is SKIPPED, not queued, so a slow round quietly loses the round behind it.
9. **Unattended cron has no approver: `python3 -c`, heredocs and inline `$(...)` are BLOCKED.** Four
   refusals in one sweep left packs holding only jd.md. Write the helper and run `python3 <path>`.
10. **Never stage this work on the operator's machine.** The habit came from skill text claiming a laptop
    fallback: it produced divergent trees and a stale credential copy. Stream content to the VM and keep
    scratch in the VM's `~/job-hunt-scratch/`.
11. **A sub-agent's report is a self-report.** Verify the tracker rows and the ledger before calling a run
    successful: a run that reported "5 applications" had 0 new applied-notes.
"""


def fix_dashes(prompt: str) -> str:
    for old, new, label in DASH_FIXES:
        if old in prompt:
            prompt = prompt.replace(old, new)
            print(f"    dash fix applied: {label}")
    return prompt


def strip_lessons(prompt: str) -> str:
    i = prompt.find(LESSONS_MARK)
    return prompt[:i].rstrip() + "\n" if i >= 0 else prompt


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")
    targets = [("template", pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json"),
                "{{SLUG}}-job-hunt")]
    for slug in ("vishal", "nhung"):
        targets.append((slug, pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/cron/jobs.json"),
                        f"{slug}-job-hunt"))

    for label, path, jobname in targets:
        data = json.loads(path.read_text(encoding="utf-8"))
        jobs = data if isinstance(data, list) else data["jobs"]
        job = [j for j in jobs if j["name"] == jobname][0]
        before = len(job["prompt"])
        prompt = strip_lessons(fix_dashes(job["prompt"]))
        dashes = sum(prompt.count(c) for c in (EM, EN))
        print(f"  {label}: {before} -> {len(prompt)} chars | dashes {dashes} | "
              f"inline lessons {'removed' if LESSONS_MARK not in prompt else 'STILL THERE'}")
        if apply and prompt != job["prompt"]:
            shutil.copy2(path, path.with_name(path.name + f".bak-finalfix-{STAMP}"))
            job["prompt"] = prompt
            body = data if isinstance(data, list) else data
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)

    # the lessons body goes into the playbook every prompt already points at
    repo_lessons = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/references/lessons.md")
    text = repo_lessons.read_text(encoding="utf-8")
    if "Incidents (22-23 Sep 2026)" in text:
        print("  playbook: incidents already present in engine/references/lessons.md")
    else:
        print(f"  playbook: appending incidents ({len(text)} -> {len(text) + len(LESSON_BODY)} chars)")
        if apply:
            shutil.copy2(repo_lessons, repo_lessons.with_name(repo_lessons.name + f".bak-incidents-{STAMP}"))
            repo_lessons.write_text(text.rstrip() + "\n" + LESSON_BODY, encoding="utf-8")
        text = text.rstrip() + "\n" + LESSON_BODY

    for slug in ("vishal", "nhung"):
        dest = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/workspace/references/lessons.md")
        if not dest.parent.is_dir():
            print(f"  {slug}: workspace has no references/ dir - skipped")
            continue
        if apply:
            dest.write_text(text, encoding="utf-8")
            print(f"  {slug}: references/lessons.md updated ({dest.stat().st_size} bytes)")
        else:
            print(f"  {slug}: would write references/lessons.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
