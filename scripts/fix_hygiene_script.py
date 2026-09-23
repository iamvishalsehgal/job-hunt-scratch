import pathlib

P = pathlib.Path("/home/ubuntu/job-hunt-scratch/offpeak_and_hygiene.py")
lines = P.read_text(encoding="utf-8").splitlines()
out = []
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.strip().startswith("clean = clean.strip() +"):
        out.append('        clean = clean.strip() + chr(10)')
        i += 1
        continue
    out.append(ln)
    i += 1
P.write_text("\n".join(out) + "\n", encoding="utf-8")
import ast
ast.parse(P.read_text(encoding="utf-8"))
print("patched and parses")
