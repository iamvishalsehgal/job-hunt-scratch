#!/usr/bin/env python3
"""Write the 22-23 Sep incident lessons where the agents that caused them will read them.

Every lesson here cost a real sweep: a role lost, a command that crashed, a throttle that stuck, or work
staged on the wrong machine. Each one states the rule and the measurement that produced it.

Usage: write_lessons.py [--prompts]
"""
import json
import pathlib
import shutil
import sys
import time

MARKER = "## LESSONS FROM THE 22-23 SEP INCIDENTS (hard - each one cost a real sweep)"
STAMP = time.strftime("%Y%m%d-%H%M%S")

LESSONS = MARKER + """

1. **A code-guard refusal is a TO-DO, not a verdict.** Measured 22 Sep: a 169-word body (cap 150) and a
   quoted EUR 60,000 (standing quote EUR 4,400-5,000) parked four winnable roles as Blocked. Cut the body to
   120 words, drop the figure, render the missing files, then run the same command again - at most twice.
   Blocked is only for a role with no drivable portal AND no real address.
2. **A pack holding only `jd.md` is an unfinished pack, never a Blocked role.** Write `tailoring.json`,
   render `cv.pdf` + `cover-letter.pdf` for THAT role first; `tools/jt.py apply-email` refuses an unbuilt
   pack by design, and the refusal is the instruction to build it.
3. **Before deploying a ported prompt, verify every file and command it names exists for THAT candidate.**
   A port carried `accounts.py --company ...` (account-gating helper) into a workspace where the file did
   not exist. Check the paths first: `for p in <paths in the prompt>; do test -e $p; done`.
4. **After any prompt swap, grep for every hotfix added since the previous version.** A port silently moved
   the CRON-SAFE EXECUTION section from a `##` heading to a `###` subsection - a heading check alone called
   it present. Grep the actual fix phrases, not the headings.
5. **A throttle driven by a row STATUS must read the row's own notes and release when the event is past.**
   Four rows sat in Interview state (two finished, one held) and held the whole pipeline at 40% for ten
   days, because nothing closes a row but the owner. Scope date parsing to interview words: a contract end
   date in the same note (`Contract runs to 2026-12-03`) read as a live interview until 3 Dec.
6. **When you add a kind or a route, update EVERY map that enumerates them.** A new `reply` kind was added
   to the mail tool but not to `jt.py`'s route-to-row map, which crashed the command with
   `KeyError: 'replied'` on the first real reply. Grep the old list everywhere (status maps, help strings,
   the check report, docs) and update the tests that assert it.
7. **A behaviour change that contradicts an earlier hard rule ships behind a per-candidate dial.** Replies
   to employers were forbidden outright; the dial (`application_email.allow_reply`) turns them on for one
   candidate only, and the default stays a refusal. Never loosen a rule for everyone to fix one account.
8. **Measure a run's real duration before raising its cadence.** A 20-minute sweep on a 10-minute schedule
   only works because the fire-claim fences overlap; the claim TTL is 300s, and a missed slot is SKIPPED,
   not queued - so a slow round quietly loses the round behind it.
9. **Unattended cron has no approver: `python3 -c`, heredocs and inline `$(...)` are BLOCKED.** Measured:
   four refusals in one sweep, and the packs it was building ended up holding only `jd.md`. Write the helper
   into `~/job-hunt-scratch/` and run `python3 <path>`.
10. **Never stage VM work on the operator's machine.** The habit came from skill text claiming a laptop
    fallback and a "synced copy of the Mac project": it produced two divergent trees and a stale credential
    copy. Stream content to the VM (`ssh ... 'cat > path' < file`) and keep scratch in the VM's
    `~/job-hunt-scratch/`.
11. **A sub-agent's own report is a self-report.** Verify the tracker rows and the ledger before calling a
    run successful: the run that reported "5 applications" had 0 new `Applied <date>` notes.
"""

TARGETS = [
    "/home/ubuntu/.hermes/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/vishal/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/nhung/skills/productivity/job-application/SKILL.md",
]


def main() -> int:
    wrote = []
    for target in TARGETS:
        p = pathlib.Path(target)
        if not p.is_file():
            print("SKIP", target)
            continue
        text = p.read_text(encoding="utf-8")
        if MARKER in text:
            print("already present:", target)
            continue
        shutil.copy2(p, p.with_name(p.name + f".bak-lessons-{STAMP}"))
        p.write_text(text.rstrip() + "\n\n" + LESSONS, encoding="utf-8")
        wrote.append(target)
        print(f"lessons written: {target} ({len(text)} -> {len(p.read_text(encoding='utf-8'))} chars)")

    if "--prompts" in sys.argv:
        for profile in ("vishal", "nhung"):
            path = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{profile}/cron/jobs.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            job = [j for j in data["jobs"] if j["name"].endswith("job-hunt")][0]
            if MARKER in job["prompt"]:
                print(f"{profile}: prompt already carries the lessons")
                continue
            shutil.copy2(path, path.with_name(path.name + f".bak-lessons-{STAMP}"))
            job["prompt"] = job["prompt"].rstrip() + "\n\n" + LESSONS
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)
            print(f"{profile}: lessons appended to the sweep prompt ({len(job['prompt'])} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
