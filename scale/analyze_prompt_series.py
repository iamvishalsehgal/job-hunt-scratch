#!/usr/bin/env python3
"""Prompt-size history vs measured per-sweep input tokens."""
import json, re, pathlib, collections, datetime

HOME = pathlib.Path.home()
PROF = HOME / ".hermes/profiles"

def prompt_len(path, suffix):
    try:
        d = json.loads(pathlib.Path(path).read_text())
    except Exception as e:
        return None
    jobs = d["jobs"] if isinstance(d, dict) else d
    for j in jobs:
        if str(j.get("name","")).endswith(suffix):
            return len(j.get("prompt") or "")
    return None

print("=== job-hunt prompt size history (from cron store + backups) ===")
series = []
for prof in ("vishal","nhung"):
    files = sorted((PROF/prof/"cron").glob("jobs.json*"))
    for f in files:
        if ".lock" in f.name: continue
        n = prompt_len(f, "job-hunt")
        if n is None: continue
        mt = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")
        series.append((mt, prof, f.name, n))
for mt, prof, name, n in sorted(series):
    print("  %s  %-7s %-46s %7d chars" % (mt, prof, name[:46], n))

print()
print("=== sweep sessions, chronological, with measured first-call input tokens ===")
LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ INFO \[(?P<sess>\S+)\] "
                  r"agent\.conversation_loop: API call #(?P<n>\d+): .*in=(?P<in>\d+) out=(?P<out>\d+) "
                  r".*cache=(?P<cache>\d+)/(?P<in2>\d+)")
JH = {}
for prof in ("vishal","nhung"):
    d = json.loads((PROF/prof/"cron"/"jobs.json").read_text())
    for j in d["jobs"]:
        if str(j.get("name","")).endswith("job-hunt"):
            JH[j["id"]] = (prof, len(j.get("prompt") or ""))
print("  job-hunt ids:", JH)
now = {}
for prof in ("vishal","nhung"):
    log = PROF/prof/"logs"/"agent.log"
    if not log.is_file(): continue
    for ln in log.read_text(errors="replace").splitlines():
        m = LINE.match(ln)
        if not m: continue
        g = m.groupdict()
        now.setdefault(g["sess"], []).append((int(g["n"]), int(g["in"]), int(g["out"]), int(g["cache"])))
rows=[]
for sess, calls in now.items():
    for jid,(prof,plen) in JH.items():
        if sess.startswith("cron_%s_" % jid):
            calls.sort()
            ts = sess.split("_")[-2]
            rows.append((ts, prof, calls[0][1], len(calls), sum(c[1] for c in calls),
                         sum(c[3] for c in calls), sum(c[2] for c in calls), plen))
rows.sort()
for ts, prof, first_in, nc, s_in, s_cached, s_out, plen in rows:
    print("  %s %-7s first_in=%6d calls=%3d sum_in=%8d cached=%8d uncached=%7d out=%6d prompt=%6d"
          % (ts, prof, first_in, nc, s_in, s_cached, s_in-s_cached, s_out, plen))
