import ast, pathlib, shutil, datetime, sys, re

p = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace/build_tracker.py")
src = p.read_text(encoding="utf-8")
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bak = p.with_suffix(".py.bak-coolblue-" + stamp)
shutil.copy2(p, bak)

text = (" | Receipt 2026-09-23 00:25 UTC (notification@careersatcoolblue.com, inbox 184579): "
        "'Hebbes! Je sollicitatie voor de functie van Analytics Engineer is binnen' - SmartRecruiters "
        "auto-receipt confirming this portal submission; no action required, no reply sent.")
assert '"' not in text

start = src.index("coolblue-analytics-engineer")
end = src.index('"],', start)
assert src[end] == '"', src[end:end + 5]
assert src.count("coolblue-analytics-engineer") == 1
new = src[:end] + text + src[end:]

ast.parse(new)
mod = ast.parse(new)
rows = None
for node in mod.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "applications" for t in node.targets):
        rows = ast.literal_eval(node.value)
assert rows is not None
hits = [r for r in rows if str(r[1]).startswith("Coolblue")]
print("rows:", len(rows), "coolblue:", [(r[0], r[1], r[2], r[4], len(r[11])) for r in hits])
assert hits and hits[0][11].endswith("no reply sent."), hits[0][11][-80:]

p.write_text(new, encoding="utf-8")
print("written", p, "backup", bak.name)
