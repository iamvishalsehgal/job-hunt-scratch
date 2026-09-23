import json, collections, datetime, os

ws = "/home/ubuntu/.hermes/profiles/vishal/workspace"
p = os.path.join(ws, "data/apply-email-ledger.json")
d = json.load(open(p))
recs = d["records"] if isinstance(d, dict) else d
print("total recs", len(recs))
print("keys", sorted(recs[0].keys()))
print(collections.Counter((r.get("kind"), r.get("ok")) for r in recs))
print("---- ok applications ----")
for r in recs:
    if r.get("ok") and r.get("kind") == "application":
        ts = r.get("sent_at") or r.get("ts") or r.get("date") or r.get("time")
        print(ts, "|", r.get("company"), "|", r.get("role"), "|", r.get("application"), "|", r.get("ids"))
print("---- ok follow-ups ----")
for r in recs:
    if r.get("ok") and r.get("kind") == "follow-up":
        ts = r.get("sent_at") or r.get("ts") or r.get("date") or r.get("time")
        print(ts, "|", r.get("company"), "|", r.get("role"))
print("---- failures ----")
for r in recs:
    if not r.get("ok"):
        print(r.get("kind"), "|", r.get("company"), "|", r.get("role"), "|", str(r.get("error"))[:120])
