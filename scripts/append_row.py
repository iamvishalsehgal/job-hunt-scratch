#!/usr/bin/env python3
"""Append ONE results line to a run's results.tsv (tab separated, no header).

Usage:
  python3 append_row.py <results_file> <slug> <outcome> <evidence> <note> <attachments> \
        <jd_path> <apply_url> <route>

finished_utc is generated here (UTC, YYYY-MM-DDTHH:MM:SSZ). Never rewrites the file.
"""
import datetime
import sys

COLS = ["slug", "outcome", "evidence", "note", "attachments", "jd_path", "apply_url", "route"]


def main() -> int:
    if len(sys.argv) != 10:
        print(__doc__)
        return 2
    path = sys.argv[1]
    vals = [a.replace("\t", " ").replace("\n", " ").strip() for a in sys.argv[2:10]]
    vals = [v if v else "-" for v in vals]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = "\t".join(vals + [stamp]) + "\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
    print("appended:", line.rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
