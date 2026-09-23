#!/usr/bin/env python3
"""Sync the 23 Sep hotfixes into the tenant TEMPLATE, so a NEW tenant gets them too.

The two live prompts were patched by hand during the session; the template they are rendered from was
not, so a fresh account would provision with '3 pack agents', 'Deferred (agent cap)' and no
volume/refusal/lessons rules. Also appends the 11 incident lessons, and makes the employer-mail
parenthetical reply-aware instead of claiming a reply is never sent.

Idempotent. Usage: sync_template_hotfixes.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
TEMPLATE = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json")
NAME = "{{SLUG}}-job-hunt"

UNLIMITED = """
## UNLIMITED PLAN: VOLUME AND CADENCE (owner rule, 23 Sep 2026)

This candidate's model plan is UNLIMITED. Cost is NEVER a reason to skip a role, defer a batch, shorten a
pack, or take a lighter route through one. The only reasons a role is dropped are the hard gates
(sponsorship, local-language fluency, closed vacancy) and the tracker rules - never money.

- THIS JOB RUNS EVERY 10 MINUTES and each run is a full sweep that continues where the last one stopped.
- AT LEAST 30 APPLICATIONS PER ROUND (Submitted + Emailed together), or every eligible role when fewer
  than 30 clear the gates. A round that lands 30 and stops is a good round; the next one picks up the
  backlog. Discoveries that do not fit become "Queued (next round)" - the phrase "Deferred (agent cap)"
  must not appear while fewer than 30 have been applied this round.
- BUDGET: up to 8 pack agents per sweep, each holding a batch of 4 roles. The old cap of 3 exists in the
  cost notes below and is OVERRIDDEN by this rule, not deleted: batch for speed, never to save money.
- IF A RUN IS STILL GOING WHEN THE NEXT IS DUE, finish it: the scheduler will not start a second one, so
  keep the batch tight and write each role's tracker row as it finishes.

"""

FIXRETRY = """
## WHEN A GATE REFUSES, FIX THE DRAFT AND SEND AGAIN (owner rule, 23 Sep 2026)

A refusal is a STATEMENT OF WHAT TO FIX, never a verdict on the role. Measured 22 Sep 2026: four roles in
one sweep ended Blocked because a draft was 169 words (cap 150) and another quoted EUR 60,000 (the
standing quote is EUR 4,400-5,000). Both refusals name the fix; both roles were winnable. NEVER park a
role as Blocked while the refusal is about the DRAFT - Blocked is only for a role with no drivable portal
AND no real address anywhere (record CONTACT DISCOVERY's result in the Notes).

Fix, then run the SAME command again:
- `the body is N words; the cap is 150` -> cut the body to 120 words or fewer, keep the `Wants:` line and
  one evidence line per ask, drop everything else, send again.
- `quotes EUR X but the candidate's standing quote is ...` -> delete the figure entirely (best) or use the
  standing range. NEVER invent or inflate a band, never quote the posting's own range as the candidate's.
- `no tailoring.json` / `missing cv.pdf` / `missing cover-letter.pdf` -> render them for THIS role first
  (`make_pdfs.py <slug>` in the workspace), then send. A pack holding only jd.md is an unfinished pack,
  never a Blocked role.
- `no address` / `guessed domain` / `placeholder` -> run CONTACT DISCOVERY once; with a real address, send;
  without one, the row is BROWSER NEEDED.
- `already sent` from the ledger -> that IS the answer: record the row, never resend.
At most TWO fix-and-resend attempts per role per round. If the second attempt is still refused, write the
refusal text into that row's Notes so the next round can fix it - a refusal never silently becomes Blocked.

"""

LESSONS = """
## LESSONS FROM THE 22-23 SEP INCIDENTS (hard - each one cost a real sweep)

1. **A code-guard refusal is a TO-DO, not a verdict.** Measured 22 Sep: a 169-word body (cap 150) and a
   quoted EUR 60,000 parked four winnable roles as Blocked. Cut the body, drop the figure, render the
   missing files, run the same command again - at most twice.
2. **A pack holding only `jd.md` is unfinished, never a Blocked role.** Write `tailoring.json` and render
   `cv.pdf` + `cover-letter.pdf` for THAT role first; the tool's refusal is the instruction to build it.
3. **Before deploying a ported prompt, verify every file and command it names exists for THIS candidate.**
   A port carried an account-gating helper into a workspace where the file did not exist. Test the paths.
4. **After any prompt swap, grep for every hotfix added since the previous version, not just the headings.**
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


def patch_prompt(p: str) -> str:
    edits = [
        ("at most 3 pack agents per sweep ({{FULL_NAME}}: 4), plus at most 1 discovery agent",
         "at most 8 pack agents per sweep (8 x batch-size 4 = 32 roles), plus at most 2 discovery agents",
         "cap 3/1 -> 8/2 and drop the per-name clause"),
        ('the note "Deferred (agent cap)"', 'the note "Queued (next round)"', "deferral note"),
        ("no change in volume or routing. (employer mail is capped: one application, one follow-up, never a reply to an employer.)",
         "no change in volume or routing. (Employer mail is capped: one application, one follow-up, and "
         "where the account's own dial allows it one reply per incoming employer message - see the "
         "OUTBOUND MAIL section. Never a second follow-up, never a cold reply.)",
         "reply-aware mail parenthetical"),
        ("## SUB-AGENT DISCIPLINE",
         UNLIMITED.lstrip("\n") + FIXRETRY.lstrip("\n") + "## SUB-AGENT DISCIPLINE",
         "UNLIMITED PLAN + WHEN A GATE REFUSES"),
    ]
    for old, new, label in edits:
        n = p.count(old)
        if n == 0:
            print(f"  skip {label} (absent - already applied?)")
            continue
        print(f"  ok   {label} x{n}")
        p = p.replace(old, new)
    if "LESSONS FROM THE 22-23 SEP INCIDENTS" in p:
        print("  skip lessons appendix (already present)")
    else:
        p = p.rstrip() + "\n" + LESSONS
        print("  ok   lessons appendix")
    return p


def main() -> int:
    apply = "--apply" in sys.argv
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    job = [x for x in data if x["name"] == NAME][0]
    before = len(job["prompt"])
    prompt = patch_prompt(job["prompt"])
    print(f"template prompt: {before} -> {len(prompt)} chars")
    for marker in ("UNLIMITED PLAN", "WHEN A GATE REFUSES", "LESSONS FROM THE 22-23 SEP",
                   "({{FULL_NAME}}: 4)", "Deferred (agent cap)", "never a reply to an employer"):
        print(f"   {'PRESENT' if marker in prompt else 'ABSENT ':8} {marker}")
    if not apply:
        print("DRY RUN (pass --apply)")
        return 0
    shutil.copy2(TEMPLATE, TEMPLATE.with_name(TEMPLATE.name + f".bak-templatesync-{STAMP}"))
    job["prompt"] = prompt
    tmp = TEMPLATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(TEMPLATE)
    print("written;", len([x for x in data if x.get('name')]), "job templates intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
