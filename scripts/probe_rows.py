#!/usr/bin/env python3
import json
import pathlib

RUN = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace/runs/2026-09-23h")
d = json.loads((RUN / "roles.json").read_text())
roles = d if isinstance(d, list) else d.get("roles", d)
want = ("ilionx-ai", "farm-frites", "momentum-agentic", "info-support-senior")
for r in roles:
    if str(r.get("slug", "")).startswith(want):
        print(json.dumps(r, ensure_ascii=False)[:1000])
print("keys:", list(roles[0].keys()) if roles else None, "n=", len(roles))
man = json.loads((RUN / "batch-manifest.json").read_text())
print("manifest:", json.dumps(man, ensure_ascii=False)[:600])
