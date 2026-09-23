#!/usr/bin/env python3
"""Fetch LinkedIn guest JDs for pack batch 1 (2026-09-23g) and write per-slug jd.md."""
import html as h
import pathlib
import re
import subprocess

ROOT = pathlib.Path("/home/ubuntu/Desktop/job-hunt")
ROLES = {
    "deloitte-junior-data-engineer": ("4457796644", "Deloitte", "Junior Data Engineer", "Amsterdam"),
    "sogeti-medior-data-engineer": ("4466214395", "Sogeti", "Medior Data Engineer", "Groningen"),
    "info-support-data-engineer": ("4447078253", "Info Support", "Data Engineer", "Veenendaal"),
    "ventolines-medior-data-engineer": ("4470444039", "Ventolines", "Medior Data Engineer", "Almere"),
}
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")


def fetch(jid):
    url = f"https://www.linkedin.com/jobs-guest/jobs/view/{jid}"
    r = subprocess.run(["curl", "-s", "-L", "-A", UA, "--max-time", "30", url],
                       capture_output=True, text=True, timeout=45)
    return r.stdout


def clean(s):
    s = re.sub(r"<li[^>]*>", "\n- ", s)
    s = re.sub(r"</(li|p|div|h\d|br)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = h.unescape(s)
    s = s.replace("\u2014", " - ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


for slug, (jid, co, role, loc) in ROLES.items():
    page = fetch(jid)
    t = re.search(r"<title>([^<]*)</title>", page)
    title = h.unescape(t.group(1)) if t else ""
    m = re.search(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>\s*</div>', page, re.S)
    if not m:
        m = re.search(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*)', page, re.S)
    desc = clean(m.group(1))[:9000] if m else ""
    crit = re.findall(r'description__job-criteria-text[^>]*>([^<]*)</span>', page)
    pm = re.search(r'posted relative-time="([^"]+)"', page)
    d = ROOT / "applications" / slug
    d.mkdir(parents=True, exist_ok=True)
    head = [f"# {role} - {co} ({loc})", "",
            f"Source: https://nl.linkedin.com/jobs/view/{jid}",
            f"Page title: {title}",
            f"Posted: {pm.group(1) if pm else 'n/a'}",
            f"Criteria: {' / '.join(c.strip() for c in crit)}", "",
            desc, ""]
    (d / "jd.md").write_text("\n".join(head), encoding="utf-8")
    print("=====", slug, "| html", len(page))
    print("TITLE:", title, "| POSTED:", pm.group(1) if pm else "?",
          "| CRIT:", " / ".join(c.strip() for c in crit))
    print("DESC:", desc[:1500].replace("\n", " | "))
    print()
