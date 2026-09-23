"""Verify the pack batch 2 outputs: TSV shape, no em/en dashes in materials."""
import pathlib

RUN = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace/runs/2026-09-23g/results.tsv")
APPS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace/applications")
for i, line in enumerate(RUN.read_text(encoding="utf-8").splitlines()):
    parts = line.split("\t")
    print(i, "fields:", len(parts), parts[0][:44])
bad = []
for s in ["itility-data-engineer", "aurea-imaging-data-engineer",
          "datacation-data-engineer", "alfen-data-engineer"]:
    for f in sorted((APPS / s).iterdir()):
        if f.suffix in (".md", ".txt", ".json"):
            t = f.read_text(encoding="utf-8")
            if "\u2014" in t or "\u2013" in t:
                bad.append(str(f))
print("dash-hits:", bad)
