#!/usr/bin/env python3
"""Measure where a sweep"s tokens go, from the agent logs. No guessing."""
import re, sys, json, pathlib, collections

LINE = re.compile(
    r"^(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ INFO \[(?P<sess>\S+)\] "
    r"agent\.conversation_loop: API call #(?P<n>\d+): model=(?P<model>\S+) provider=\S+ "
    r"in=(?P<in>\d+) out=(?P<out>\d+) total=(?P<total>\d+) latency=(?P<lat>[\d.]+)s "
    r"cache=(?P<cache>\d+)/(?P<in2>\d+) \((?P<pct>\d+)%\)"
)

def stats(path, label):
    sessions = collections.OrderedDict()
    for ln in pathlib.Path(path).read_text(errors="replace").splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        d = m.groupdict()
        sessions.setdefault(d["sess"], []).append({
            "n": int(d["n"]), "in": int(d["in"]), "out": int(d["out"]),
            "cache": int(d["cache"]), "total": int(d["total"]), "lat": float(d["lat"]),
        })
    rows = []
    for s, calls in sessions.items():
        calls.sort(key=lambda c: c["n"])
        rows.append({
            "sess": s, "calls": len(calls),
            "first_in": calls[0]["in"], "peak_in": max(c["in"] for c in calls),
            "sum_in": sum(c["in"] for c in calls),
            "sum_cached": sum(c["cache"] for c in calls),
            "sum_out": sum(c["out"] for c in calls),
            "sum_lat": round(sum(c["lat"] for c in calls), 1),
            "first_ts": s[:13],
        })
    rows.sort(key=lambda r: -r["sum_in"])
    return label, rows

if __name__ == "__main__":
    out = {}
    for label, path in [("vishal", pathlib.Path.home()/".hermes/profiles/vishal/logs/agent.log"),
                        ("nhung", pathlib.Path.home()/".hermes/profiles/nhung/logs/agent.log")]:
        if not path.is_file():
            print(label, "MISSING", path); continue
        lab, rows = stats(path, label)
        out[lab] = rows
        print("=== %s : %d sessions with logged API calls ===" % (lab, len(rows)))
        big = [r for r in rows if r["first_in"] > 30000]
        print("  sessions whose FIRST call already carries >30k tokens (sweep-like): %d" % len(big))
        print("  %-24s %5s %9s %9s %10s %11s %8s" % ("session","calls","first_in","peak_in","sum_in","sum_cached","sum_out"))
        for r in rows[:12]:
            print("  %-24s %5d %9d %9d %10d %11d %8d" % (r["sess"], r["calls"], r["first_in"], r["peak_in"], r["sum_in"], r["sum_cached"], r["sum_out"]))
        if big:
            n=len(big)
            print("  --- aggregates over sweep-like sessions ---")
            print("  calls/session avg      : %.1f" % (sum(r["calls"] for r in big)/n))
            print("  sum_in/session avg     : %.0f" % (sum(r["sum_in"] for r in big)/n))
            print("  sum_out/session avg    : %.0f" % (sum(r["sum_out"] for r in big)/n))
            print("  cache hit share        : %.1f%%" % (100.0*sum(r["sum_cached"] for r in big)/sum(r["sum_in"] for r in big)))
            print("  uncached in/session avg: %.0f" % (sum(r["sum_in"]-r["sum_cached"] for r in big)/n))
        print()
    pathlib.Path.home().joinpath("job-hunt-scratch/scale/session_stats.json").write_text(json.dumps(out, indent=1))
