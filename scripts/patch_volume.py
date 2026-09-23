#!/usr/bin/env python3
"""Owner rule, 23 Sep 2026: both candidates are on UNLIMITED plans.

- the sweep runs every 10 minutes (was every 180), the mail job every 10 (was 20)
- every round applies AT LEAST 30 jobs (was a 5-15 target with a 3-pack-agent cap)
- the pack-agent cap goes 3 -> 8, so 8 x batch-size 4 = 32 roles per run
- discovery widens: every tier-1 country gets the full keyword matrix, two tier-2 countries per run
- an EU top-up rule fills a short round when the Dutch market cannot supply 30
- the employer-email ceilings (code-enforced) go 1/5 -> 30/40 for vishal

Usage: patch_volume.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
PROFILES = ("vishal", "nhung")

UNLIMITED = """
## UNLIMITED PLAN: VOLUME AND CADENCE (owner rule, 23 Sep 2026)

The model plan for this candidate is UNLIMITED. Cost is NEVER a reason to skip a role, defer a batch,
shorten a pack, or take a cheaper/lighter route through one. The only reasons a role is dropped are the
hard gates (sponsorship, Dutch fluency, closed vacancy) and the tracker rules - never money.

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


def sub(text, old, new, label, required=True):
    n = text.count(old)
    if n != 1:
        if required:
            raise SystemExit(f"REFUSED: anchor for {label} appears {n} times, expected 1")
        print(f"  skip {label} ({n} occurrences)")
        return text
    print(f"  ok   {label}")
    return text.replace(old, new)


def patch_prompt(prompt, profile):
    print(f"--- {profile}: prompt {len(prompt)} chars")
    prompt = sub(prompt, "(nhung: 4), ", "", "stale nhung cap clause", required=False)
    prompt = sub(prompt,
                 "at most 3 pack agents per sweep",
                 "at most 8 pack agents per sweep (8 x batch-size 4 = 32 roles)",
                 "pack-agent cap 3 -> 8")
    prompt = sub(prompt,
                 "at most 1 discovery agent",
                 "at most 2 discovery agents",
                 "discovery agents 1 -> 2")
    prompt = sub(prompt,
                 'the note "Deferred (agent cap)"',
                 'the note "Queued (next round)"',
                 "deferral note")
    prompt = sub(prompt,
                 "A full sweep should produce 5-15 applications, most of them AUTO.",
                 "A full sweep MUST produce AT LEAST 30 applications (Submitted + Emailed), or every "
                 "eligible role when fewer than 30 clear the gates - see UNLIMITED PLAN below.",
                 "round volume target")
    prompt = sub(prompt, "swept ONE country per run", "swept TWO countries per run",
                 "tier-2 rotation 1 -> 2 countries")
    prompt = sub(prompt, "the NEXT one in the pool", "the next TWO in the pool", "rotation cursor text")
    prompt = sub(prompt,
                 "DISCOVERY BUDGET: NL gets the full keyword matrix (every keyword x offsets 0/25/50). The EU pass gets",
                 "DISCOVERY BUDGET (unlimited plan): NL AND every tier-1 country gets the full keyword matrix "
                 "(every keyword x offsets 0/25/50). Only the two rotating tier-2 countries get",
                 "discovery budget widened")
    prompt = sub(prompt,
                 "the Priority-1 keywords only and a reduced offset set",
                 "the priority keywords only and a reduced offset set",
                 "discovery budget tail",
                 required=False)
    prompt = sub(prompt,
                 "  the priority keywords only and a reduced offset set:",
                 "  the priority keywords only and a reduced offset set:",
                 "discovery budget tail 2",
                 required=False)
    prompt = sub(prompt,
                 "- ORDER: work the NL queue FIRST and COMPLETELY",
                 "- TOP-UP RULE (owner rule, 23 Sep 2026): the 80/20 split is the TARGET, never a ceiling on "
                 "the round. If fewer than 30 NL roles clear the gates, fill the rest of the 30 from tier-1 EU "
                 "countries and report the measured split honestly - never end a round short to protect the "
                 "ratio.\n- ORDER: work the NL queue FIRST and COMPLETELY",
                 "EU top-up rule")
    prompt = sub(prompt, "## SUB-AGENT DISCIPLINE", UNLIMITED + "\n## SUB-AGENT DISCIPLINE",
                 "unlimited-plan section")
    return prompt


def patch_jobs(profile):
    path = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{profile}/cron/jobs.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    shutil.copy2(path, path.with_name(path.name + f".bak-volume-{STAMP}"))
    changed = []
    for job in data["jobs"]:
        if job["name"].endswith("job-hunt"):
            prompt = patch_prompt(job["prompt"], profile)
            job["prompt"] = prompt
            job["schedule"] = {"kind": "interval", "minutes": 10, "display": "every 10m"}
            job["schedule_display"] = "every 10m"
            changed.append((job["name"], 10))
        elif job["name"].endswith("-mail"):
            job["schedule"] = {"kind": "interval", "minutes": 10, "display": "every 10m"}
            job["schedule_display"] = "every 10m"
            changed.append((job["name"], 10))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(path)
    print(f"  jobs updated: {changed}")
    return changed


def patch_notify(profile):
    """The employer-email ceilings are code-enforced; raise them so a 30-application round can use the route."""
    path = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{profile}/workspace/notify.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    ae = data.get("application_email") or {}
    if not ae.get("enabled"):
        print(f"  {profile}: employer email is OFF by rule - caps left alone")
        return
    shutil.copy2(path, path.with_name(path.name + f".bak-volume-{STAMP}"))
    ae["max_per_run"] = 30
    ae["max_per_day"] = 40
    data["application_email"] = ae
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"))
    print(f"  {profile}: email ceilings -> max_per_run=30 max_per_day=40")


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN (pass --apply to write)")
    for profile in PROFILES:
        if apply:
            patch_jobs(profile)
            patch_notify(profile)
        else:
            path = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{profile}/cron/jobs.json")
            job = [j for j in json.loads(path.read_text())["jobs"] if j["name"].endswith("job-hunt")][0]
            patch_prompt(job["prompt"], profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
