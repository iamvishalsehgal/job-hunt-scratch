#!/usr/bin/env python3
"""Give nhung's prompt the LESSONS pointer her workspace already supports.

The prompt split correctly moved the LESSONS section to <workspace>/references/lessons.md where a section
existed - vishal's did, nhung's never had one ('## LESSONS (distilled from the job skills)' was absent from
her prompt). Her workspace therefore carried a lessons.md (including the 22-23 Sep incidents) that nothing
in her prompt ever told her to read. This adds the pointer in the same shape as the other seven.

Usage: add_lessons_pointer.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
P = pathlib.Path("/home/ubuntu/.hermes/profiles/nhung/cron/jobs.json")
POINTER = """## LESSONS (distilled from the job skills and the live incidents)
PLAYBOOK: read {{WORKSPACE}}/references/lessons.md before you route an application, pick an ATS route, or handle a rejection. It carries every rule this section used to carry, plus the 22-23 Sep incident log. The live path is below the placeholder when this prompt is rendered.

"""
RENDERED = POINTER.replace("{{WORKSPACE}}", "/home/ubuntu/.hermes/profiles/nhung/workspace")


def main() -> int:
    apply = "--apply" in sys.argv
    data = json.loads(P.read_text(encoding="utf-8"))
    job = [j for j in data["jobs"] if j["name"].endswith("job-hunt")][0]
    prompt = job["prompt"]
    if "references/lessons.md" in prompt:
        print("already points at the playbook")
        return 0
    anchor = "## SUB-AGENT DISCIPLINE"
    if anchor not in prompt:
        print("REFUSED: no anchor")
        return 1
    block = POINTER if "{{WORKSPACE}}" in prompt else RENDERED
    prompt = prompt.replace(anchor, block + anchor, 1)
    print(f"nhung: {len(job['prompt'])} -> {len(prompt)} chars")
    if apply:
        shutil.copy2(P, P.with_name(P.name + f".bak-lessonsptr-{STAMP}"))
        job["prompt"] = prompt
        tmp = P.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(P)
        print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
