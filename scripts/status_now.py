#!/usr/bin/env python3
"""One-screen status: per candidate, the sweep job's cadence state and today's applied count."""
import ast
import collections
import json
import pathlib
import re


def main() -> int:
    for slug in ("vishal", "nhung"):
        data = json.loads(pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/cron/jobs.json").read_text())
        job = [x for x in data["jobs"] if x["name"].endswith("job-hunt")][0]
        print("%-7s last=%s status=%s next=%s running=%s every=%s" % (
            slug, str(job["last_run_at"])[:19], job["last_status"],
            str(job["next_run_at"])[:19], bool(job.get("fire_claim")), job["schedule_display"]))
        src = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/workspace/build_tracker.py").read_text(errors="replace")
        tree = ast.parse(src)
        rows = next(ast.literal_eval(n.value) for n in ast.walk(tree)
                    if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "applications" for t in n.targets))
        dates = collections.Counter()
        for r in rows:
            for m in re.findall(r"Applied (20\d\d-\d\d-\d\d)", str(r[11])):
                dates[m] += 1
        recent = ", ".join(f"{k}:{v}" for k, v in sorted(dates.items())[-3:])
        print("        rows=%d | applied %s | %s" % (
            len(rows), recent, dict(collections.Counter(str(r[5]) for r in rows))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
