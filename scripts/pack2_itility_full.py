"""Fetch the full Itility posting text (own board) and re-run dutch_gate on it."""
import pathlib
import re
import subprocess
import urllib.request

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
OUT = WS / "applications" / "itility-data-engineer"

req = urllib.request.Request("https://careers.itility.nl/o/data-engineer",
                             headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
print("html bytes", len(html))
body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
body = re.sub(r"(?s)<[^>]+>", "\n", body)
body = re.sub(r"&nbsp;?", " ", body)
body = re.sub(r"&amp;", "&", body)
body = re.sub(r"[ \t]+", " ", body)
body = re.sub(r"\n\s*\n+", "\n", body).strip()
print("text bytes", len(body))
low = body.lower()
for probe in ["nederlands", "beheersing", "vloeiend", "communicatieve"]:
    idx = [m.start() for m in re.finditer(probe, low)]
    print(probe, len(idx), [re.sub(r"\s+", " ", body[max(0, i - 70):i + 90]) for i in idx[:3]])

(OUT / "jd-full.txt").write_text(body[:20000], encoding="utf-8")
r = subprocess.run(["python3", "gates/dutch_gate.py", str(OUT / "jd-full.txt")],
                   capture_output=True, text=True, cwd="/home/ubuntu/Desktop/job-hunt")
print("gate rc", r.returncode, r.stdout.strip(), r.stderr.strip()[:200])
