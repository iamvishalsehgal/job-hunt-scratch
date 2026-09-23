#!/usr/bin/env python3
"""Show context around each detail link and around location words in an ApplicantStack listing."""
import html
import re
import sys

path = sys.argv[1]
kw = sys.argv[2:] or ["botlek", "nld", "netherlands"]
h = open(path, encoding="utf-8", errors="replace").read()
t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
plain = html.unescape(re.sub(r"<[^>]+>", " ", t))
plain = re.sub(r"\s+", " ", plain)
for k in kw:
    print(f"=== {k} ===")
    for m in re.finditer(k, plain, re.I):
        print("   ...", plain[max(0, m.start() - 160):m.end() + 160], "...")
print("=== per detail link (raw) ===")
for m in re.finditer(r"href=\"(https://tronox\.applicantstack\.com/x/detail/[^\"]+)\"", h):
    url = m.group(1)
    seg = h[max(0, m.start() - 700):m.end() + 700]
    seg = html.unescape(re.sub(r"<[^>]+>", " ", seg))
    print(url, ">>>", re.sub(r"\s+", " ", seg)[:400])
