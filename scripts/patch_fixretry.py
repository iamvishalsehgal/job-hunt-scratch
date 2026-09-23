#!/usr/bin/env python3
"""Owner rule, 23 Sep 2026: a guard refusal is a to-do, not a verdict.

Measured in the 21:34 sweep: roles died as Blocked because the DRAFT failed a code guard - a 169-word
body (cap 150) and a quoted EUR 60,000 (standing quote EUR 4,400-5,000). Both refusals name their own
fix, and both roles were winnable. This adds the fix-and-resend rule to both candidates' prompts.

Usage: patch_fixretry.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
SECTION = """
## WHEN A GATE REFUSES, FIX THE DRAFT AND SEND AGAIN (owner rule, 23 Sep 2026)

A refusal is a STATEMENT OF WHAT TO FIX, never a verdict on the role. Measured 22 Sep 2026: four roles in
one sweep ended Blocked because a draft was 169 words (cap 150) and another quoted EUR 60,000 (his standing
quote is EUR 4,400-5,000). Both refusals name the fix; both roles were winnable. NEVER park a role as
Blocked while the refusal is about the DRAFT - Blocked is only for a role with no drivable portal AND no
real address anywhere (record CONTACT DISCOVERY's result in the Notes).

Fix, then run the SAME command again:
- `the body is N words; the cap is 150` -> cut the body to 120 words or fewer (leave margin), keep the
  `Wants:` line and one evidence line per ask, drop everything else, send again.
- `quotes EUR X but the candidate's standing quote is EUR 4,400-5,000` -> delete the figure entirely (best)
  or use the standing range. NEVER invent or inflate a band, never quote the posting's own range as his.
- `no tailoring.json` / `missing cv.pdf` / `missing cover-letter.pdf` -> render them for THIS role first
  (tailor-cv + make_pdfs make_pdfs.py <slug> in the workspace), then send. A pack holding only jd.md is an
  unfinished pack, never a Blocked role.
- `no address` / `guessed domain` / `placeholder` -> run CONTACT DISCOVERY once; with a real address, send;
  without one, the row is BROWSER NEEDED.
- `already sent` from the ledger -> that IS the answer: record the row, never resend.
At most TWO fix-and-resend attempts per role per round. If the second attempt is still refused, write the
refusal text into that row's Notes so the next round can fix it - a refusal never silently becomes Blocked.

"""

OLD_TAIL = """  than 30 clear the gates. A round that lands 30 and stops is a good round; the next one picks up the
  backlog. Discoveries that do not fit become "Queued (next round)" - the phrase "Deferred (agent cap)"
  must not appear while fewer than 30 have been applied this round."""

NEW_TAIL = OLD_TAIL + """
- BLOCKED IS A LAST RESORT: a round's rows are Submitted or Emailed. "Blocked" is allowed only when a role
  has no drivable portal AND no real address (see WHEN A GATE REFUSES)."""


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")
    for profile in ("vishal", "nhung"):
        path = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{profile}/cron/jobs.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        job = [j for j in data["jobs"] if j["name"].endswith("job-hunt")][0]
        prompt = job["prompt"]
        if "WHEN A GATE REFUSES" in prompt:
            print(f"{profile}: already patched")
            continue
        if prompt.count("## SUB-AGENT DISCIPLINE") != 1 or OLD_TAIL not in prompt:
            raise SystemExit(f"REFUSED: anchors missing in {profile}")
        prompt = prompt.replace(OLD_TAIL, NEW_TAIL)
        prompt = prompt.replace("## SUB-AGENT DISCIPLINE", SECTION + "\n## SUB-AGENT DISCIPLINE", 1)
        print(f"{profile}: {len(job['prompt'])} -> {len(prompt)} chars "
              f"| fix-retry section: {'WHEN A GATE REFUSES' in prompt} | blocked-last: {'BLOCKED IS A LAST RESORT' in prompt}")
        if apply:
            shutil.copy2(path, path.with_name(path.name + f".bak-fixretry-{STAMP}"))
            job["prompt"] = prompt
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)
            print(f"  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
