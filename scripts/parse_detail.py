#!/usr/bin/env python3
"""Summarise an ApplicantStack detail page: title, location, apply link, form/captcha hints."""
import html
import re
import sys

path = sys.argv[1]
h = open(path, encoding="utf-8", errors="replace").read()
t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()
print("PLAIN-FIRST-600:", plain[:600])
print()
for m in re.finditer(r"(NLD|Botlek|Job Location|Location|Job Function|Job Title)[^|]{0,120}", plain, re.I):
    print("CTX:", m.group(0)[:160])
print()
print("--- forms ---")
for m in re.finditer(r"<form[^>]*>", h, re.I):
    print(m.group(0)[:300])
print("--- apply links ---")
for m in re.finditer(r"href=\"([^\"]*(?:apply|/x/[^\"]*)\"|[^\"]*apply[^\"]*)", h, re.I):
    print(m.group(1)[:200])
print("--- inputs ---")
for m in re.finditer(r"<input[^>]*>", h, re.I):
    print(re.sub(r"\s+", " ", m.group(0))[:220])
print("--- textareas/selects ---")
for m in re.finditer(r"<(?:textarea|select)[^>]*>", h, re.I):
    print(re.sub(r"\s+", " ", m.group(0))[:220])
print("--- keywords ---")
low = h.lower()
for k in ("captcha", "recaptcha", "hcaptcha", "turnstile", "cloudflare", "file", "resume", "upload"):
    print(f"{k}: {low.count(k)}")
