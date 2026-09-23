import pathlib

rows = [
    {
        "slug": "lleverage-forward-deployed-ai-engineer",
        "outcome": "rejected",
        "evidence": "inbox 184586 and 184587 - recruiter Tim Beyer (recruitment@lleverage.ai), 2026-09-23: pursuing candidates whose experience and skills align more closely with the role; no interview was held",
        "note": "pre-interview rejection of the emailed application (Recruitee form was captcha-walled, so the pack went by email 2026-09-14); no action, no follow-up, no ping",
        "attachments": "",
        "jd_path": "",
        "apply_url": "",
        "route": "email",
        "finished": "2026-09-23T05:06:00Z",
        "company": "Lleverage",
        "role": "Forward Deployed AI Engineer",
        "location": "Amsterdam, Netherlands",
        "fit": "3.0",
    },
    {
        "slug": "info-support-data-engineer",
        "outcome": "submitted",
        "evidence": "auto-receipt 2026-09-23 02:13 UTC from the Info Support recruitment team (Teamtailor): application for Data Engineer received in good order; a Teamtailor email-verification mail for the same application arrived 02:11 UTC",
        "note": "row created from the receipt - the submitting run left no row; IND sponsor confirmed on Info Support B.V.; posted start EUR 3,400 gross per month, below the 4k target",
        "attachments": "cv.pdf, cover-letter.pdf",
        "jd_path": "applications/info-support-data-engineer/jd.md",
        "apply_url": "https://werkenbij.infosupport.com/jobs/5728947-data-engineer",
        "route": "own careers site (werkenbij.infosupport.com)",
        "finished": "2026-09-23T02:13:00Z",
        "company": "Info Support",
        "role": "Data Engineer",
        "location": "Veenendaal, Netherlands",
        "fit": "4.2",
    },
]

order = ["slug", "outcome", "evidence", "note", "attachments", "jd_path", "apply_url",
         "route", "finished", "company", "role", "location", "fit"]
out = pathlib.Path("/home/ubuntu/job-hunt-scratch/mail-results.tsv")
lines = []
for r in rows:
    for k in order:
        v = str(r.get(k, ""))
        assert "\t" not in v and "\n" not in v, k
    lines.append("\t".join(r[k] for k in order))
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out.read_text(encoding="utf-8")[:400])
print("lines:", len(lines))
