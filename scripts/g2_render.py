#!/usr/bin/env python3
"""Render cv.pdf + cover-letter.pdf for the batch-1 (wave 2) packs."""
import pathlib, subprocess, sys

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
CO = pathlib.Path.home() / "career-ops"


def run(cmd, cwd=WS):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=600)
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out[-400:]


for slug in sys.argv[1:]:
    pack = WS / "applications" / slug
    tj = pack / "tailoring.json"
    print("=" * 8, slug)
    if not tj.exists():
        print("  no tailoring.json - skip")
        continue
    rc, out = run(["python3", str(CO / "scripts" / "tailor-cv.py"), str(tj), slug])
    print("  tailor rc", rc, "|", out.replace("\n", " ")[:250])
    rc, out = run(["python3", str(WS / "make_pdfs.py"), slug])
    print("  pdfs rc", rc, "|", out.replace("\n", " ")[:250])
    cl = pack / "cover-letter.md"
    if cl.exists():
        rc, out = run(["node", str(CO / "cover-pdf.mjs"), str(cl), str(pack / "cover-letter.pdf")])
        print("  cover rc", rc, "|", out.replace("\n", " ")[:200])
    for f in ("cv.pdf", "cover-letter.pdf", "cv.html"):
        p = pack / f
        print("   ", f, p.stat().st_size if p.exists() else "MISSING")
