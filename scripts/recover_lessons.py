#!/usr/bin/env python3
"""Restore the section body my overwrite dropped from vishal's references/lessons.md.

diagnosis: syncing the incident lessons to the workspace copies overwrote each workspace's
references/lessons.md with the ENGINE's copy. For vishal the workspace copy held the moved body of the old
'## LESSONS (distilled from the job skills ...)' section (it mentions him by name), and the engine copy did
not. The body is still in the pre-move cron backup, so recover it from there and append it, keeping the
incidents that were just added.

Usage: recover_lessons.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
SECTION_HEAD = "## LESSONS (distilled from the job skills"
WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace/references/lessons.md")


def section_body(prompt: str) -> str:
    i = prompt.find(SECTION_HEAD)
    if i < 0:
        return ""
    start = prompt.index("\n", i) + 1
    nxt = prompt.find("\n## ", start)
    return prompt[start:nxt if nxt > 0 else len(prompt)].strip("\n")


def main() -> int:
    apply = "--apply" in sys.argv
    store = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/cron/jobs.json")
    baks = sorted(store.parent.glob("jobs.json.bak-playbook-*"))
    if not baks:
        print("no pre-move backup found")
        return 2
    old = [j for j in json.loads(baks[-1].read_text(encoding="utf-8"))["jobs"]
           if j["name"].endswith("job-hunt")][0]["prompt"]
    body = section_body(old)
    print(f"recovered body: {len(body)} chars from {baks[-1].name}")
    current = WS.read_text(encoding="utf-8")
    if "Walled role: never emailed when the portal failed" in current:
        print("already present")
        return 0
    merged = current.rstrip() + "\n\n## The rules this section used to carry inline\n\n" + body + "\n"
    print(f"merge: {len(current)} -> {len(merged)} chars")
    if apply:
        shutil.copy2(WS, WS.with_name(WS.name + f".bak-recover-{STAMP}"))
        WS.write_text(merged, encoding="utf-8")
        print("written", WS)
    else:
        print("DRY RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
