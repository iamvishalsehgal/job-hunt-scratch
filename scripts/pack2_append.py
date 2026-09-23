import pathlib
import datetime

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
R = WS / "runs/2026-09-23h/results.tsv"
UTC = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
L = "/home/ubuntu/.hermes/profiles/vishal/workspace/applications"
LI = "https://nl.linkedin.com/jobs/view/"

rows = [
    (
        "9altitudes-netherlands-young-data-professional-traineeship-data-bi",
        "skipped",
        'dutch_gate rc=10 SKIP_DUTCH_FLUENCY; posting requires "Je spreekt vloeiend Nederlands (at least C1)"',
        "Hard skip rule 4(a): Dutch at C1 for a client-facing BI traineeship in Veenendaal (posting fully Dutch, Power BI/SQL/DAX/Fabric content would otherwise fit). IND sponsor 9altitudes Nederland B.V. on register line 54. No salary figure published. No CV, no letter, no email spent.",
        f"{L}/9altitudes-netherlands-young-data-professional-traineeship-data-bi/jd.md,{L}/9altitudes-netherlands-young-data-professional-traineeship-data-bi/fit.md,{L}/9altitudes-netherlands-young-data-professional-traineeship-data-bi/apply-url.txt",
        f"{L}/9altitudes-netherlands-young-data-professional-traineeship-data-bi/jd.md",
        LI + "young-data-professional-traineeship-data-bi-at-9altitudes-netherlands-4447143704",
        "LinkedIn guest view + gates/dutch_gate.py, hard skip 4(a) Dutch C1, nothing submitted",
    ),
    (
        "axians-nl-trainee-bi-consultant",
        "skipped",
        'dutch_gate rc=10 SKIP_DUTCH_FLUENCY; "Je spreekt Nederlands en Engels"; startsalaris EUR 2.700 per month',
        "Two independent blockers: Dutch required (rule 4(a), Dutch posting and client projects in Zorg/Retail/Onderwijs/Overheid) and the stated gross of EUR 2.700 per month is below the EUR 3.300 floor, so the salary filter fails too. IND sponsor Axians Communication Solutions B.V. on register line 1054. No CV, no letter, no email spent.",
        f"{L}/axians-nl-trainee-bi-consultant/jd.md,{L}/axians-nl-trainee-bi-consultant/fit.md,{L}/axians-nl-trainee-bi-consultant/apply-url.txt",
        f"{L}/axians-nl-trainee-bi-consultant/jd.md",
        LI + "trainee-bi-consultant-at-axians-nl-4335462709",
        "LinkedIn guest view + gates/dutch_gate.py, hard skip (Dutch) plus below-floor salary, nothing submitted",
    ),
    (
        "tmc-bi-consultant",
        "skipped",
        'dutch_gate rc=10 SKIP_DUTCH_FLUENCY; requirement line "Goede beheersing van Nederlands en Engels"',
        "Hard skip rule 4(a): good command of Dutch required for client-facing BI consultancy in Eindhoven. Skills otherwise a strong match (Power BI, SQL, Azure, data modelling, 1-5 yrs asked). TMC Employeneurship is a permanent TMC employment contract, so the ZZP rule is not the blocker. IND TMC Data Science B.V./TMC Digital & IT B.V. on register lines 11458-11459. No salary published. No CV, no letter, no email spent.",
        f"{L}/tmc-bi-consultant/jd.md,{L}/tmc-bi-consultant/fit.md,{L}/tmc-bi-consultant/apply-url.txt",
        f"{L}/tmc-bi-consultant/jd.md",
        LI + "bi-consultant-at-tmc-4470466508",
        "LinkedIn guest view + gates/dutch_gate.py, hard skip 4(a) Dutch, nothing submitted",
    ),
    (
        "funda-medior-backend-net-engineer",
        "blocked",
        "jobs.funda.nl apply form (Recruitee) renders a live hCaptcha enclave (captcha-assets.recruiteecdn.com .../hcaptcha-enclave.html) and captchaToken field; no submit attempted, by rule",
        "BROWSER NEEDED: https://jobs.funda.nl/o/medior-backend-net-engineer/c/new?lang=en | contact hunt: jobs.funda.nl, funda.nl, the posting text and web search show no recruitment mailbox (posting refuses agency contact and unsolicited CVs), so no address passed gates/email_guard.py | CAPTCHA wall on submit, one page check only, no workaround | Deferred (interview in progress), EMAIL SEND DISABLED, no PDF spend per PACK_RULES section 10 | dutch_gate rc=0 (fluent English, Dutch a plus), posted EUR 4.512,23-6.083,64/mo clears the filters, Amsterdam hybrid, IND sponsor Funda Real Estate B.V. on register line 4358 | .NET/C# and Kubernetes are his stated gaps (Python/Flask and Azure are his production stack)",
        f"{L}/funda-medior-backend-net-engineer/jd.md,{L}/funda-medior-backend-net-engineer/cover-letter.md,{L}/funda-medior-backend-net-engineer/tailoring.json,{L}/funda-medior-backend-net-engineer/fit.md,{L}/funda-medior-backend-net-engineer/email-to-hr.md,{L}/funda-medior-backend-net-engineer/apply-url.txt",
        f"{L}/funda-medior-backend-net-engineer/jd.md",
        "https://jobs.funda.nl/o/medior-backend-net-engineer/c/new?lang=en",
        "Funda own board (Recruitee) - hCaptcha-walled on submit, no submit attempted, deferred while interviews pending",
    ),
]

with R.open("a") as fh:
    for slug, outcome, ev, note, att, jd, url, route in rows:
        for field in (slug, outcome, ev, note, att, jd, url, route, UTC):
            assert "\t" not in field and "\n" not in field, field[:40]
        fh.write("\t".join([slug, outcome, ev, note, att, jd, url, route, UTC]) + "\n")
        print("appended", slug)

print("--- results.tsv now ---")
print(R.read_text())
print("--- WROTE sizes ---")
for p in sorted(APPS.rglob("*")):
    if p.is_file() and any(s in str(p) for s in ("9altitudes-netherlands", "axians-nl-trainee-bi", "tmc-bi-consultant", "funda-medior-backend")):
        if "tmc-bi-consultant" in str(p) or "trainee-bi" in str(p) or "9altitudes-netherlands" in str(p) or "funda-medior-backend" in str(p):
            print(f"WROTE {p} {p.stat().st_size}")
print(f"WROTE {R} {R.stat().st_size}")
