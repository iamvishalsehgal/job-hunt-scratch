import subprocess, sys, os, json, re
from datetime import datetime, timezone

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
RES = os.path.join(WS, "discovery/_sweep-2026-09-23f-g2/results.tsv")
APPS = os.path.join(WS, "applications")
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run(cmd):
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

mail = run([sys.executable, "gates/otp_fetch.py", "--from", "myworkday.com", "--within", "25"])
print("MAIL:", mail[:400])
receipt = bool(re.search(r"basic-?fit|club data analyst", mail, re.I)) and bool(re.search(r"receipt|confirm", mail, re.I))
print("RECEIPT_FOR_BASICFIT:", receipt)

lines = []
bf_evidence = ("Workday apply completed on Basic-Fit's own board (basicfit.wd103 R55713): 5 steps filled and reviewed, "
               "Submit clicked, no error returned")
if receipt:
    bf_evidence += "; Workday confirmation mail received"
lines.append([
 "basic-fit-club-data-analyst", "submitted", bf_evidence,
 "Applied 2026-09-23; own board resolved from the LinkedIn mirror (no Easy Apply); CV + motivation letter uploaded; "
 "motivation and salary questions answered, salary quoted 4,400 (posted band EUR 3,500-5,500 gross/month, top below the 5k target); "
 "IND sponsor confirmed; no account needed",
 ",".join([os.path.join(APPS, "basic-fit-club-data-analyst", f) for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")]),
 os.path.join(APPS, "basic-fit-club-data-analyst/jd.md"),
 "https://basicfit.wd103.myworkdayjobs.com/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713",
 "workday-own-board-accountless-browser-submit", now])

lines.append([
 "jpmorganchase-software-engineer-iii-databricks", "blocked",
 "Oracle Recruiting Cloud apply is hCaptcha-walled: email + consent filled, NEXT does not advance, hCaptcha challenge iframe present; stopped without touching the challenge",
 "BROWSER NEEDED: https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210768004 | "
 "contact hunt: careers.jpmorgan.com and jpmorganchase.com contact/recruitment-privacy pages fetched, no mailbox published, no address passed email_guard; "
 "IE role so no manual hand-off allowed",
 ",".join([os.path.join(APPS, "jpmorganchase-software-engineer-iii-databricks", f) for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")]),
 os.path.join(APPS, "jpmorganchase-software-engineer-iii-databricks/jd.md"),
 "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210768004",
 "oracle-recruiting-cloud-captcha-walled", now])

lines.append([
 "euronext-data-engineer-for-ai", "blocked",
 "Workday tenant hrhub.wd3: reached Create Account (step 1 of 5) via /apply/applyManually, filled email + password + consent, Create Account does not submit and no verification mail arrives; no error shown, no code in the mailbox",
 "BROWSER NEEDED: https://hrhub.wd3.myworkdayjobs.com/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530/apply | "
 "contact hunt: euronext.com careers and contact pages fetched, no mailbox published, no address passed email_guard; IE role so no manual hand-off allowed",
 ",".join([os.path.join(APPS, "euronext-data-engineer-for-ai", f) for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")]),
 os.path.join(APPS, "euronext-data-engineer-for-ai/jd.md"),
 "https://hrhub.wd3.myworkdayjobs.com/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530",
 "workday-account-creation-not-drivable", now])

lines.append([
 "salesforce-data-engineering-senior-associate", "blocked",
 "Workday tenant salesforce.wd12: posting live (JR359930) but the account-gated apply flow could not be driven in this session after the hrhub.wd3 tenant showed the same silent Create Account failure",
 "BROWSER NEEDED: https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930/apply | "
 "contact hunt: salesforce.com careers/contact/legal pages fetched, no mailbox published, no address passed email_guard; IE role so no manual hand-off allowed",
 ",".join([os.path.join(APPS, "salesforce-data-engineering-senior-associate", f) for f in ("cv.pdf", "cover-letter.pdf", "cover-letter.md", "tailoring.json", "fit.md", "email-to-hr.md")]),
 os.path.join(APPS, "salesforce-data-engineering-senior-associate/jd.md"),
 "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930",
 "workday-account-gate-not-drivable", now])

with open(RES, "a") as fh:
    for row in lines:
        fh.write("\t".join(row).replace("\n", " ") + "\n")
print("APPENDED", len(lines))
print(open(RES).read()[-1200:])
