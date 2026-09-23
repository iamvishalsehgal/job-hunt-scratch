import os, re, json, subprocess, sys

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
RAW = os.path.expanduser("~/job-hunt-scratch/jd_raw")
APPS = os.path.join(WS, "applications")

META = {
 "euronext-data-engineer-for-ai": ("euronext", "Euronext", "Data Engineer for AI", "Dublin, Ireland",
   "https://hrhub.wd3.myworkdayjobs.com/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530", "Live 2026-09-18, Workday hrhub.wd3 tenant"),
 "salesforce-data-engineering-senior-associate": ("salesforce", "Salesforce", "Data Engineering Senior Associate", "Ireland - Dublin",
   "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930", "Live 2026-09-22, JR359930, Workday salesforce.wd12 tenant"),
 "basic-fit-club-data-analyst": ("basicfit", "Basic-Fit", "Club Data Analyst", "Hoofddorp, Netherlands",
   "https://basicfit.wd103.myworkdayjobs.com/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713", "Live 2026-09-15, R55713, own board basicfit.wd103 Workday tenant (resolved from the LinkedIn mirror)"),
}
for slug, (key, comp, role, loc, url, note) in META.items():
    body = open(os.path.join(RAW, key + ".txt")).read()
    d = os.path.join(APPS, slug)
    os.makedirs(d, exist_ok=True)
    txt = (f"# {role} - {comp}\n\n"
           f"- Company: {comp}\n- Role: {role}\n- Location: {loc}\n- Apply URL: {url}\n"
           f"- Verified live on the employer's own board: {note}\n"
           f"- Captured: 2026-09-23 (from the employer's own ATS API, posting text verbatim)\n\n"
           f"## Posting text\n\n{body}\n")
    open(os.path.join(d, "jd.md"), "w").write(txt)
    print("wrote", os.path.join(d, "jd.md"), len(txt))

print("--- gate ---")
for slug in ("jpmorganchase-software-engineer-iii-databricks", "euronext-data-engineer-for-ai",
             "salesforce-data-engineering-senior-associate"):
    p = os.path.join(APPS, slug, "jd.md")
    if not os.path.exists(p):
        print(slug, "NO JD YET"); continue
    r = subprocess.run([sys.executable, "gates/eu_scope_gate.py", "check", "--country", "IE", "--jd", p],
                       cwd=WS, capture_output=True, text=True)
    print(slug, "exit", r.returncode, "|", (r.stdout + r.stderr).strip()[:300])
print("--- excerpts ---")
for k in ("euronext", "salesforce"):
    t = open(os.path.join(RAW, k + ".txt")).read()
    print("#####", k, len(t))
    print(t[:3600])
