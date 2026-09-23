#!/usr/bin/env python3
"""Bound the cron fan-out (scale-audit finding 3).

`cron.max_parallel_jobs` was unset in all three configs, so the scheduler fell back to the ThreadPoolExecutor
default (8 concurrent jobs per gateway) while each sweep spawns 8 pack agents + 2 discovery agents and drives
headless browsers. On a 4-OCPU box already at load 5.1 that is a stampede waiting to happen.

This sets a ceiling that still lets one sweep run beside the mail/publish/sync jobs, and never queues a sweep
behind a copy of itself (a per-job run is already fenced by the fire-claim).

Usage: set_fanout.py [--apply]
"""
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
LIMIT = 4
TARGETS = (
    pathlib.Path("/home/ubuntu/.hermes/config.yaml"),
    pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/config.yaml"),
    pathlib.Path("/home/ubuntu/.hermes/profiles/nhung/config.yaml"),
)
NOTE = """  # Bound the fan-out: each sweep spawns 8 pack agents + 2 discovery agents and drives browsers, so an
  # unbounded default (8 concurrent jobs/gateway) stampedes a 4-OCPU box. 4 lets a sweep run beside the
  # mail, publish and sync jobs without queueing a job behind a copy of itself.
  max_parallel_jobs: {limit}
""".format(limit=LIMIT)


def main() -> int:
    apply = "--apply" in sys.argv
    for path in TARGETS:
        if not path.is_file():
            print(f"  SKIP {path} (absent)")
            continue
        lines = path.read_text(encoding="utf-8").splitlines(True)
        if any(l.strip().startswith("max_parallel_jobs:") for l in lines):
            print(f"  {path}: already set")
            continue
        out, done, in_cron = [], False, False
        for line in lines:
            if not done and in_cron and not line.startswith((" ", "\t", "-")):
                out.append(NOTE)
                done = True
            out.append(line)
            if line.rstrip() == "cron:":
                in_cron = True
        if not done:
            out.append("\ncron:\n" + NOTE)
            print(f"  {path}: no cron block found - appended one")
        if apply:
            shutil.copy2(path, path.with_name(path.name + f".bak-fanout-{STAMP}"))
            path.write_text("".join(out), encoding="utf-8")
            print(f"  {path}: max_parallel_jobs = {LIMIT}")
        else:
            print(f"  {path}: would add max_parallel_jobs: {LIMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
