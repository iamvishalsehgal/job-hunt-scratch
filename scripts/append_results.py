#!/usr/bin/env python3
"""Append job-hunt result rows to a results.tsv (tab separated, no header).

Usage: python3 append_results.py <results.tsv> <records.jsonl>

records.jsonl holds one JSON array per line, one array per result row, whose items are the
columns in order:
  slug, outcome, evidence, note, attachments, jd_path, apply_url, route, finished_utc

Tabs and newlines inside a field are collapsed to spaces so a row can never break the file.
"""
import json
import sys
from pathlib import Path

COLS = ["slug", "outcome", "evidence", "note", "attachments", "jd_path", "apply_url", "route", "finished_utc"]


def clean(v):
    return " ".join(str(v).replace("\t", " ").replace("\r", " ").split())


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    target = Path(sys.argv[1])
    records = Path(sys.argv[2])
    rows = []
    for line in records.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        fields = json.loads(line)
        if len(fields) != len(COLS):
            raise SystemExit("record has %d fields, expected %d: %s" % (len(fields), len(COLS), line[:120]))
        rows.append("\t".join(clean(f) for f in fields))
    with target.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(row + "\n")
    print("appended %d row(s) to %s" % (len(rows), target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
