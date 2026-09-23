#!/usr/bin/env python3
"""Fetch the employer's own-board capture of the Info Support Senior Data Engineer posting,
strip it to text, then run gates/dutch_gate.py on it (the canonical capture for the verdict)."""
import html
import pathlib
import re
import subprocess
import sys
import urllib.request

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
OUT = pathlib.Path.home() / "job-hunt-scratch" / "is-sde-own.txt"
URL = "https://carriere.infosupport.com/vacatures/senior-data-engineer"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; jobhunt/1.0)"})
raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
body = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
body = re.sub(r"(?s)<[^>]+>", " ", body)
text = re.sub(r"&nbsp;?", " ", html.unescape(body))
text = re.sub(r"[ \t\r\f\v]+", " ", text)
text = re.sub(r"\n\s*\n+", "\n", text).strip()
OUT.write_text(text)
print("saved", OUT, len(text), "chars")

r = subprocess.run([sys.executable, str(WS / "gates" / "dutch_gate.py"), "--json", str(OUT)],
                   capture_output=True, text=True)
print("own-board gate:", r.stdout.strip(), "rc=", r.returncode)
r2 = subprocess.run([sys.executable, str(WS / "gates" / "dutch_gate.py"), "--json",
                     str(WS / "applications" / "info-support-senior-data-engineer" / "jd.md")],
                    capture_output=True, text=True)
print("linkedin-mirror gate:", r2.stdout.strip(), "rc=", r2.returncode)
