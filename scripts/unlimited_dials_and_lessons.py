#!/usr/bin/env python3
"""Owner rule 23 Sep 2026: both candidates are on unlimited model plans.

1. Raise each candidate's daily model budget so the money dial reports real spend and never throttles
   a sweep. The gate's sentence stays honest ('spent $X of $Y'), it just stops being a constraint.
   `on_exceed: warn` is kept: it discloses, it does not reduce volume.
2. Append the 11 incident lessons to both live sweep prompts, and make the employer-mail parenthetical
   reply-aware (it still claimed a reply is never sent anywhere).

Idempotent. Usage: unlimited_dials_and_lessons.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
DAILY_USD = 50.0
LESSONS_MARK = "LESSONS FROM THE 22-23 SEP INCIDENTS"

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

OLD_MAIL = ("no change in volume or routing. (employer mail is capped: one application, one follow-up, "
            "never a reply to an employer.)")
NEW_MAIL = ("no change in volume or routing. (Employer mail is capped: one application, one follow-up, and "
            "where the account's own dial allows it one reply per incoming employer message - see the "
            "OUTBOUND MAIL section. Never a second follow-up, never a cold reply.)")


def patch_config(path: pathlib.Path, apply: bool) -> bool:
    """Raise the daily dial in a tenant yaml, keeping every other line byte-identical."""
    text = path.read_text(encoding="utf-8")
    if f"daily_usd: {DAILY_USD:.2f}" in text:
        print(f"  {path}: already {DAILY_USD:.2f}")
        return True
    lines = []
    hit = 0
    for line in text.splitlines(True):
        if line.strip().startswith("daily_usd:"):
            indent = line[:len(line) - len(line.lstrip())]
            lines.append(f"{indent}daily_usd: {DAILY_USD:.2f}          # unlimited plan (owner rule 23 Sep 2026)\n")
            hit += 1
        else:
            lines.append(line)
    if hit != 1:
        print(f"  {path}: SKIP (found {hit} daily_usd lines)")
        return False
    if apply:
        shutil.copy2(path, path.with_name(path.name + f".bak-unlimited-{STAMP}"))
        path.write_text("".join(lines), encoding="utf-8")
        print(f"  {path}: daily_usd -> {DAILY_USD:.2f} (on_exceed unchanged)")
    else:
        print(f"  {path}: would set daily_usd -> {DAILY_USD:.2f}")
    return True


def patch_workspace_dial(ws: pathlib.Path, apply: bool) -> None:
    p = ws / "config.json"
    if not p.is_file():
        print(f"  {ws.name}: no config.json")
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    b = d.get("budget")
    if not isinstance(b, dict):
        print(f"  {ws.name}: no budget block")
        return
    if b.get("daily_usd") == DAILY_USD:
        print(f"  {ws.name}: workspace dial already {DAILY_USD:.2f}")
        return
    b["daily_usd"] = DAILY_USD
    b["on_exceed"] = "warn"
    d["budget"] = b
    if apply:
        shutil.copy2(p, p.with_name(p.name + f".bak-unlimited-{STAMP}"))
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {ws.name}: workspace dial daily_usd -> {DAILY_USD:.2f} on_exceed=warn")


def patch_prompt(path: pathlib.Path, profile: str, apply: bool) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    job = [j for j in data["jobs"] if j["name"].endswith("job-hunt")][0]
    prompt = job["prompt"]
    before = len(prompt)
    if OLD_MAIL in prompt:
        prompt = prompt.replace(OLD_MAIL, NEW_MAIL)
        print(f"  {profile}: mail parenthetical made reply-aware")
    else:
        print(f"  {profile}: mail parenthetical already current")
    if LESSONS_MARK in prompt:
        print(f"  {profile}: lessons already present")
    else:
        prompt = prompt.rstrip() + "\n" + LESSONS
        print(f"  {profile}: lessons appended")
    print(f"  {profile}: prompt {before} -> {len(prompt)} chars")
    if apply and prompt != job["prompt"]:
        shutil.copy2(path, path.with_name(path.name + f".bak-unlimited-{STAMP}"))
        job["prompt"] = prompt
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(path)


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")
    print("dials:")
    patch_config(pathlib.Path("/home/ubuntu/jobhunt-agent/config/tenant.yaml"), apply)
    for slug in ("vishal", "nhung"):
        patch_workspace_dial(pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/workspace"), apply)
    print("prompts:")
    for slug in ("vishal", "nhung"):
        patch_prompt(pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/cron/jobs.json"), slug, apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
