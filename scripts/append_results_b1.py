#!/usr/bin/env python3
"""Append batch-1 results lines (sweep _sweep-2026-09-23f). Append-only, never rewrites."""
import os

OUT = "/home/ubuntu/.hermes/profiles/vishal/workspace/discovery/_sweep-2026-09-23f/results.tsv"
TS = "2026-09-23T05:31:00Z"
CACHE = "/home/ubuntu/.hermes/profiles/vishal/cache/web/"

rows = [
    [
        "abn-amro-bank-n-v-medior-data-analyst-engineer-dfc",
        "blocked",
        "vacancy 9527 live on werkenbijabnamro.nl on 2026-09-23 (Schaal 9 EUR 4,634-6,620 pm); inline apply form /solliciteren/9527/inline renders but carries a reCAPTCHA container (div#form_captcha) so it is not submittable headlessly and was not worked around",
        "No new submission: this vacancy was already applied to on 2026-09-11 by email and ABN AMRO refused that route (recruiter Wico van Spanje: ABN AMRO does not accept applications by email and will not open attachments). BROWSER NEEDED: https://www.werkenbijabnamro.nl/vacature/9527/medior-data-analyst-engineer-dfc",
        "none",
        CACHE + "www.werkenbijabnamro.nl-2f0c577b06.md",
        "https://www.werkenbijabnamro.nl/vacature/9527/medior-data-analyst-engineer-dfc",
        "own careers site (custom form, reCAPTCHA-walled) - browser needed",
        TS,
    ],
    [
        "booking-sap-data-analytics-engineer",
        "emailed",
        "application email to recruitment@booking.com sent 2026-09-22 and acknowledged by the People Team (HR case HRC0925057, mail 184564); jobs.booking.com job 30066 live and still bot-walled to headless on 2026-09-23",
        "No new send and no new submission: this vacancy is already applied to (row 439 Emailed) and a second copy is refused by rule; existing pack at applications/booking-sap-data-analytics-engineer-ii. BROWSER NEEDED: https://jobs.booking.com/booking/jobs/30066",
        "none",
        CACHE + "jobs.booking.com-41a5e2f40a33534e.cache.md",
        "https://jobs.booking.com/booking/jobs/30066",
        "email (portal 403 to headless) - already applied",
        TS,
    ],
    [
        "crystalloids-senior-analytics-engineer",
        "rejected",
        "same vacancy rejected 09 Sep 2026 by Polina Salimyanova ('no matching position available at this time'); careers/analytics-engineer/ page re-verified live on crystalloids.com on 2026-09-23",
        "No re-apply: this is the already-rejected vacancy (row 99), whose previous re-submission by a sweep is logged as DUPLICATE-SUBMIT; Mautic apply form not driven",
        "none",
        CACHE + "www.crystalloids.com-2df50da902.md",
        "https://www.crystalloids.com/careers/analytics-engineer/",
        "Mautic form (not driven - already rejected)",
        TS,
    ],
    [
        "tiqets-analytics-engineer",
        "rejected",
        "employer rejection 2026-09-22 for this Analytics Engineer vacancy (Clariva Rijkland, tiqets@emails.homerun.co, inbox 184533); the own-board apply page now reads 'Applying for this job is currently not possible.' (checked 2026-09-23)",
        "No re-apply: same vacancy, closed to new applications and already rejected; prior submission 2026-09-21 via the Homerun 4-step wizard was acknowledged. Pack: applications/tiqets-analytics-engineer",
        "none",
        CACHE + "jobs.tiqets.work-11d0a2bff6277695.cache.md",
        "https://jobs.tiqets.work/analytics-engineer/en/apply",
        "Homerun (closed to new applications)",
        TS,
    ],
]

with open(OUT, "a", encoding="utf-8") as fh:
    for r in rows:
        assert len(r) == 9, r[0]
        for field in r:
            assert "\t" not in field and "\n" not in field, r[0]
        fh.write("\t".join(r) + "\n")

print("appended", len(rows), "rows")
print("size", os.path.getsize(OUT))
