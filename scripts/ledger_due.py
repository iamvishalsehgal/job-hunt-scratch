import json, datetime, collections, os

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
led = json.load(open(os.path.join(WS, "data/apply-email-ledger.json")))
print("top keys:", list(led.keys())[:10])
msgs = None
for k, v in led.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        msgs = v
        print("list key:", k, "n=", len(v), "fields:", sorted(v[0].keys()))
        break
if msgs is None:
    print(json.dumps(led)[:800])
    raise SystemExit

now = datetime.datetime.now(datetime.timezone.utc)


def bdays_between(a, b):
    n = 0
    d = a.date()
    while d < b.date():
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


by = collections.defaultdict(list)
for m in msgs:
    key = (m.get("company", "?"), m.get("role", "?"))
    by[key].append(m)

due = []
counts = collections.Counter()
for (c, r), items in by.items():
    kinds = collections.Counter(i.get("kind", "?") for i in items)
    counts.update(kinds)
    apps = [i for i in items if i.get("kind") == "application"]
    if not apps:
        continue
    last_app = max(apps, key=lambda x: x.get("ts") or "")
    ts = last_app.get("ts") or ""
    try:
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        continue
    age = bdays_between(t, now)
    sent_fu = any(i.get("kind") == "follow-up" for i in items)
    sent_reply = any(i.get("kind") == "reply" for i in items)
    if age >= 7:
        due.append((c, r, ts[:10], round(age, 1), sent_fu, sent_reply, len(items)))

print("kinds:", dict(counts))
print("total threads:", len(by))
print("--- applications >=7 business days old ---")
for d in sorted(due, key=lambda x: x[2]):
    print(d)
print("n_due_rows:", len(due))
print("n_without_followup:", sum(1 for d in due if not d[4]))
