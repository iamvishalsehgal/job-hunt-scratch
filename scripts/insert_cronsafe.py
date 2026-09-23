#!/usr/bin/env python3
"""Stop-gap edit of the live vishal-job-hunt prompt while the full port is being written.

Two changes only, both machine-checked by deploy_prompt.py afterwards:

1. `(nhung: 4)` is a Nhung-only clause in the sub-agent cap; it does not belong in this prompt.
2. A CRON-SAFE EXECUTION rule next to SCRATCH FILES. Every cron run of this job hit the security scanner:
   `python3 -c`, heredocs and inline `$(...)` are blocked with nobody to approve them, which is why whole
   sweeps ended with packs holding nothing but jd.md. The rule tells the job how to run its own scripts.

Usage: insert_cronsafe.py <jobs.json> <out-prompt-file>
"""
import json
import pathlib
import sys

STOPGAP = """## CRON-SAFE EXECUTION (hard)

This job runs unattended, so the security scanner blocks any command whose executable body it cannot fully
resolve and there is nobody to approve it. Measured on 22 Sep 2026: four commands REFUSED this way inside a
single sweep, and the packs it was building ended up holding only jd.md - so the email fallback refused them
("no tailoring.json") and every walled role landed Blocked instead of applied.

- NEVER use `python3 -c "..."`, never a shell heredoc (`<<EOF`), never an inline `$(...)` program, never a
  pipe into an interpreter.
- Write the helper with write_file into ~/job-hunt-scratch/ (never /tmp, never a stdlib module name), then
  run it as `python3 <path>`. Same for a one-off query: a two-line script in the scratch folder is always
  cheaper than a refused command that costs a turn and returns nothing.
- One `python3 <path>` invocation per step, and read its output - a batch of small scripts beats one clever
  shell line that the scanner refuses.

"""


def main() -> int:
    jobs_path, out_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    data = json.loads(jobs_path.read_text(encoding="utf-8"))
    job = next(j for j in data["jobs"] if j.get("name") == "vishal-job-hunt")
    prompt = job["prompt"]
    before = len(prompt)
    prompt2 = prompt.replace("at most 3 pack agents per sweep (nhung: 4)",
                             "at most 3 pack agents per sweep")
    assert prompt2 != prompt, "the (nhung: 4) clause was not found - refusing to write a half edit"
    anchor = "## SCRATCH FILES (never /tmp)"
    assert anchor in prompt2, "the SCRATCH FILES anchor is missing"
    prompt3 = prompt2.replace(anchor, STOPGAP + anchor, 1)
    out_path.write_text(prompt3, encoding="utf-8")
    print(f"wrote {out_path} ({before} -> {len(prompt3)} chars)")
    print(f"  (nhung: 4) removed: {'(nhung: 4)' not in prompt3}")
    print(f"  CRON-SAFE section added: {'## CRON-SAFE EXECUTION (hard)' in prompt3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
