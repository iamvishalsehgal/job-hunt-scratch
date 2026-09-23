#!/usr/bin/env python3
"""Verify the hotfix markers and playbook pointers survive, and that a pointer's target is reachable."""
import json
import pathlib

MARKS = ["AT LEAST 30 APPLICATIONS", "WHEN A GATE REFUSES", "UNLIMITED PLAN",
         "THE EMAIL IS FORMATTED, NEVER ONE PARAGRAPH", "discovery_cache.py",
         "model_budget.py ask", "at most 8 pack agents", "Queued (next round)"]
LESSON_MARK = "Incidents (22-23 Sep 2026)"

TARGETS = [("template", pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json"), "{{SLUG}}-job-hunt")]
for slug in ("vishal", "nhung"):
    TARGETS.append((slug, pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/cron/jobs.json"), f"{slug}-job-hunt"))

for label, path, jobname in TARGETS:
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data if isinstance(data, list) else data["jobs"]
    prompt = [j for j in jobs if j["name"] == jobname][0]["prompt"]
    missing = [m for m in MARKS if m not in prompt]
    ptrs = [ln.split()[2] for ln in prompt.splitlines() if ln.startswith("PLAYBOOK: read") and len(ln.split()) > 2]
    bad = [p for p in ptrs if not pathlib.Path(p).is_file()]
    lessons_ok = any(pathlib.Path(p).is_file() and LESSON_MARK in pathlib.Path(p).read_text(encoding="utf-8")
                     for p in ptrs) or LESSON_MARK in prompt
    print("%-9s %6d chars | missing=%s | pointers=%d bad=%s | lessons_reachable=%s" % (
        label, len(prompt), missing or "none", len(ptrs), bad or "none", lessons_ok))
