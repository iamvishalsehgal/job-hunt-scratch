#!/usr/bin/env python3
"""Parse an ApplicantStack openings/listing page: print anchor labels + hrefs."""
import html
import re
import sys

path = sys.argv[1]
h = open(path, encoding="utf-8", errors="replace").read()
t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
for m in re.finditer(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", t, flags=re.S | re.I):
    url, txt = m.group(1), m.group(2)
    lab = html.unescape(re.sub(r"<[^>]+>", " ", txt))
    lab = re.sub(r"\s+", " ", lab).strip()
    if lab:
        print(f"{lab[:120]}\t{url}")
print("--- title ---")
mt = re.search(r"<title>(.*?)</title>", h, flags=re.S | re.I)
print(html.unescape(re.sub(r"\s+", " ", mt.group(1))).strip() if mt else "?")
low = h.lower()
for kw in ("captcha", "recaptcha", "hcaptcha", "princip", "botlek"):
    print(f"{kw}: {low.count(kw)}")
