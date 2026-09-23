import os, re, subprocess, sys

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
APPS = os.path.join(WS, "applications")
roles = [
 ("haskoning-bi-consultant-asset-management", "Haskoning", "BI Consultant Asset Management", "Eindhoven",
  "https://nl.linkedin.com/jobs/view/bi-consultant-asset-management-at-haskoning-4460528111"),
 ("pggm-medior-azure-devops", "PGGM", "Medior Azure DevOps", "Zeist",
  "https://nl.linkedin.com/jobs/view/medior-azure-devops-at-pggm-4468399993"),
 ("deloitte-junior-engineer-next-generation-customer-solutions", "Deloitte",
  "Junior Engineer next-generation Customer Solutions", "Amsterdam",
  "https://nl.linkedin.com/jobs/view/junior-engineer-next-generation-customer-solutions-at-deloitte-4465995041"),
 ("sogeti-medior-ai-engineer", "Sogeti", "Medior AI Engineer", "Utrecht",
  "https://nl.linkedin.com/jobs/view/medior-ai-engineer-at-sogeti-4465220731"),
]
CUT = re.compile(r"(similar jobs|people also viewed|similar searches|vergelijkbare vacatures|ook bekeken|vergelijkbare zoekopdrachten)", re.I)

for slug, comp, role, loc, url in roles:
    d = os.path.join(APPS, slug)
    raw = open(os.path.join(d, "jd-raw.txt"), encoding="utf-8", errors="replace").read()
    lines = []
    for ln in raw.splitlines():
        if CUT.search(ln.strip()):
            break
        lines.append(ln)
    body = "\n".join(lines).strip()
    hdr = (f"# JD - {comp} - {role} ({loc}, Netherlands)\n\n"
           f"apply_url: {url}\n"
           f"captured: 2026-09-23 UTC, LinkedIn guest view (title/body text) via browser\n\n"
           f"## Posting text (verbatim capture)\n\n")
    open(os.path.join(d, "jd.md"), "w", encoding="utf-8").write(hdr + body + "\n")
    print(f"== {slug}: jd.md {len(hdr)+len(body)+1} bytes, body {len(body)} chars")
    g = subprocess.run(["python3", os.path.join(WS, "gates/dutch_gate.py"),
                        os.path.join(d, "jd.md")], capture_output=True, text=True, cwd=WS)
    print("   dutch_gate rc=%d %s" % (g.returncode, (g.stdout + g.stderr).strip().replace("\n", " | ")[:200]))
    e = subprocess.run(["python3", os.path.join(WS, "gates/eu_scope_gate.py"), "check",
                        "--country", "NL", "--jd", os.path.join(d, "jd.md")],
                       capture_output=True, text=True, cwd=WS)
    print("   eu_scope rc=%d %s" % (e.returncode, (e.stdout + e.stderr).strip().replace("\n", " | ")[:200]))
    for pat in [r"salaris", r"beloning", r"€\s?[\d.,]+", r"bruto", r"Nederlandse taal", r"Dutch",
                r"sponsor", r"kennismigrant", r"jaar ervaring", r"hbo", r"wo-niveau", r"certific"]:
        hits = re.findall(r"[^\n]{0,90}" + pat + r"[^\n]{0,90}", body, re.I)
        for h in hits[:2]:
            print("   KEY:", re.sub(r"\s+", " ", h).strip()[:180])
