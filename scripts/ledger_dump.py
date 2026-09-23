import json, collections, datetime
p='/home/ubuntu/.hermes/profiles/vishal/workspace/data/apply-email-ledger.json'
d=json.load(open(p))
recs=d.get('records') or d
by=collections.defaultdict(list)
for r in recs:
    by[(r.get('company'), r.get('role'))].append((r.get('ts'), r.get('kind'), r.get('ok'), r.get('error','')[:60]))
print('records:', len(recs))
for k,v in sorted(by.items(), key=lambda kv: kv[0][0] or ''):
    for ts,kind,ok,err in sorted(v):
        print(f"{(k[0] or '')[:28]:28s} | {(k[1] or '')[:38]:38s} | {kind:12s} | {ts} | ok={ok} | {err if not ok else ''}")
print('---config---')
c=json.load(open('/home/ubuntu/.hermes/profiles/vishal/workspace/config.json'))
print(json.dumps({k:v for k,v in c.items() if 'mail' in k or 'follow' in str(k)}, indent=1)[:800])
