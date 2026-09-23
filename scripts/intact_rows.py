#!/usr/bin/env python3
"""Extract the job rows from the Intact/RSA Ireland vacancy list and show Data Engineer rows."""
import re

p = "/home/ubuntu/job-hunt-scratch/intact_vacancies.html"
h = open(p, errors="replace").read()
rows = re.findall(r'<tr><td class="searchTable_jobTitle"><a href="([^"]+)">([^<]*)</a></td>'
                  r'<td class="searchTable_location">([^<]*)</td>', h)
print("rows found: %d" % len(rows))
for url, title, loc in rows:
    t = re.sub(r"\s+", " ", title).strip()
    if any(k in t.lower() for k in ("data", "engineer", "analytics", "bi ")):
        print("  %s | %s | %s" % (t, re.sub(r"\s+", " ", loc).strip(), url))
