#!/usr/bin/env python3
"""Add company/role to the batch-3 tailoring records, show a reference pack's schema, park skip packs."""
import json
import pathlib
import shutil

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
SCRATCH = pathlib.Path.home() / "job-hunt-scratch" / "pack3-skipped"

ref = APPS / "info-support-data-engineer" / "tailoring.json"
if ref.exists():
    d = json.loads(ref.read_text())
    print("reference pack keys:", {k: (v if isinstance(v, str) else type(v).__name__) for k, v in d.items()})

for slug, company, role in [
    ("ilionx-ai-engineer", "ilionx", "AI Engineer"),
    ("info-support-senior-data-engineer", "Info Support", "Senior Data Engineer"),
]:
    p = APPS / slug / "tailoring.json"
    d = json.loads(p.read_text())
    d.setdefault("company", company)
    d.setdefault("role", role)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print("patched", p, list(d)[:4])

SCRATCH.mkdir(parents=True, exist_ok=True)
moved = []
for slug in ("farm-frites-business-intelligence-engineer", "momentum-agentic-ai-developer"):
    src = APPS / slug
    if src.exists():
        dst = SCRATCH / slug
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        moved.append(str(dst))
print("moved skips:", moved)
print("scratch contents:", sorted(p.name for p in SCRATCH.iterdir()))
