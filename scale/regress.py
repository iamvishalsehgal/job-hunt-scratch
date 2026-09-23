#!/usr/bin/env python3
"""Least-squares: first-call input tokens vs prompt chars, over real sweep sessions.
Gives a MEASURED tokens-per-char for the prompt, instead of the usual chars/4 guess."""
import json, re, pathlib, datetime, statistics

HOME = pathlib.Path.home(); PROF = HOME/".hermes/profiles"
JH = {j["id"]: (p, len(j.get("prompt") or ""))
      for p in ("vishal","nhung")
      for j in json.loads((PROF/p/"cron"/"jobs.json").read_text())["jobs"]
      if str(j.get("name","")).endswith("job-hunt")}

# prompt size history: (mtime, profile, chars)
hist = []
for p in ("vishal","nhung"):
    for f in (PROF/p/"cron").glob("jobs.json*"):
        if ".lock" in f.name: continue
        try: d = json.loads(f.read_text())
        except Exception: continue
        for j in (d["jobs"] if isinstance(d,dict) else d):
            if str(j.get("name","")).endswith("job-hunt"):
                hist.append((f.stat().st_mtime, p, len(j.get("prompt") or "")))

LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ INFO \[cron_(?P<jid>[0-9a-f]+)_(?P<ts>\d{8})_(?P<tm>\d{6})\S*\] "
                  r"agent\.conversation_loop: API call #(?P<n>\d+): .*?in=(?P<in>\d+) out=(?P<out>\d+) .*?cache=(?P<cache>\d+)/")
pts = []
for p in ("vishal","nhung"):
    log = PROF/p/"logs"/"agent.log"
    if not log.is_file(): continue
    sess = {}
    for ln in log.read_text(errors="replace").splitlines():
        m = LINE.match(ln)
        if not m: continue
        g = m.groupdict()
        if g["jid"] not in JH: continue
        sess.setdefault((g["jid"], g["ts"], g["tm"]), []).append((int(g["n"]), int(g["in"]), int(g["out"]), int(g["cache"])))
    for (jid, ts, tm), calls in sess.items():
        calls.sort()
        when = datetime.datetime.strptime(ts+tm, "%Y%m%d%H%M%S").timestamp()
        cand = [h for h in hist if h[1] == p and h[0] <= when]
        if not cand: continue
        chars = max(cand, key=lambda h: h[0])[2]
        pts.append({"prof": p, "ts": ts+tm, "chars": chars, "first_in": calls[0][1],
                    "calls": len(calls), "sum_in": sum(c[1] for c in calls),
                    "sum_cached": sum(c[3] for c in calls), "sum_out": sum(c[2] for c in calls)})

xs = [q["chars"] for q in pts]; ys = [q["first_in"] for q in pts]
mx, my = statistics.mean(xs), statistics.mean(ys)
num = sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den = sum((x-mx)**2 for x in xs)
slope = num/den; intercept = my - slope*mx
pred = [slope*x+intercept for x in xs]
ss_res = sum((y-p)**2 for y,p in zip(ys,pred)); ss_tot = sum((y-my)**2 for y in ys)
print("n sweep sessions          : %d" % len(pts))
print("slope (tokens per char)   : %.4f  -> chars per token: %.2f" % (slope, 1/slope))
print("intercept (base tokens)   : %.0f  (system + tool defs + memory, paid once per call)" % intercept)
print("R^2                       : %.3f" % (1-ss_res/ss_tot))
print()
print("%-13s %-7s %6s %8s %8s %6s %9s %9s %8s" % ("start","prof","chars","promptTk","first_in","calls","sum_in","cached","out"))
for q in sorted(pts, key=lambda q: q["ts"]):
    print("%-13s %-7s %6d %8.0f %8d %6d %9d %9d %8d" % (
        q["ts"], q["prof"], q["chars"], slope*q["chars"], q["first_in"], q["calls"], q["sum_in"], q["sum_cached"], q["sum_out"]))
json.dump({"slope":slope,"intercept":intercept,"r2":1-ss_res/ss_tot,"points":pts},
          open(str(HOME/"job-hunt-scratch/scale/regression.json"),"w"), indent=1)

# --- savings model ---
print()
print("=== prompt share of a sweep (measured) ===")
per = []
for q in pts:
    ptk = slope*q["chars"]
    per.append({"prof":q["prof"],"ts":q["ts"],"chars":q["chars"],"ptk":ptk,"calls":q["calls"],
                "sum_in":q["sum_in"],"share":ptk*q["calls"]/q["sum_in"]})
sh = [r["share"] for r in per]; c = [r["calls"] for r in per]
print("calls/sweep   median %.0f  mean %.1f  n=%d" % (statistics.median(c), statistics.mean(c), len(c)))
print("prompt tokens/turn  median %.0f" % statistics.median([r["ptk"] for r in per]))
print("prompt share of input tokens  median %.1f%%  mean %.1f%%" % (100*statistics.median(sh), 100*statistics.mean(sh)))
