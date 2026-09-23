#!/usr/bin/env python3
"""Extract the job-description text from an ApplicantStack detail page into markdown."""
import html
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8", errors="replace").read()
# keep only the main content area if it is delimited
m = re.search(r"More about this job", h, re.I)
if m:
    h = h[m.start():]
t = re.sub(r"<(script|style)\b.*?</\1>", " ", h, flags=re.S | re.I)
t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
t = re.sub(r"</(p|div|li|tr|h1|h2|h3|h4|table|ul|ol)>", "\n", t, flags=re.I)
t = re.sub(r"<li[^>]*>", "\n- ", t, flags=re.I)
t = re.sub(r"<[^>]+>", " ", t)
t = html.unescape(t)
lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in t.splitlines()]
lines = [ln for ln in lines if ln]
out = []
prev = None
for ln in lines:
    if ln == prev:
        continue
    out.append(ln)
    prev = ln
text = "\n".join(out)
# stop at the site footer
cut = text.find("Hiring Software")
if cut > 0:
    text = text[:cut]
open(dst, "w", encoding="utf-8").write(text + "\n")
print(f"wrote {dst} {len(text)} chars, {text.count(chr(10)) + 1} lines")
