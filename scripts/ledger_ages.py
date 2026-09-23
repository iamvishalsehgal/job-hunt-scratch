import json, datetime, collections

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
recs = json.load(open(WS + "/data/apply-email-ledger.json"))["records"]
ts = []
bad = 0
for r in recs:
    s = r.get("ts") or ""
    try:
        ts.append(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")))
    except Exception:
        bad += 1
ts.sort()
print("records:", len(recs), "unparsed:", bad)
if ts:
    print("oldest:", ts[0].isoformat(), "newest:", ts[-1].isoformat())
now = datetime.datetime.now(datetime.timezone.utc)
print("now:", now.isoformat())
print("records older than 7 calendar days:", sum(1 for t in ts if (now - t).days > 7))
