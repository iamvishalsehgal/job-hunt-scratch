import json, sys
p = "/home/ubuntu/.hermes/profiles/vishal/workspace/route_plan.json"
d = json.load(open(p))
slugs = ["haskoning-bi-consultant-asset-management","pggm-medior-azure-devops",
         "deloitte-junior-engineer-next-generation-customer-solutions","sogeti-medior-ai-engineer"]

def walk(o, out):
    if isinstance(o, dict):
        s = json.dumps(o)
        if any(sl in s for sl in slugs) and len(s) < 4000:
            out.append(o)
        for v in o.values():
            walk(v, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, out)

out = []
walk(d, out)
seen = set()
for o in out:
    s = json.dumps(o, sort_keys=True)
    if s in seen:
        continue
    seen.add(s)
    print(s[:1200])
    print("---")
print("TOP KEYS:", list(d.keys())[:20] if isinstance(d, dict) else len(d))
