#!/usr/bin/env python3
"""Contact hunt: harvest real mailto/email strings from the employers' own pages (evidence for email_guard)."""
import re, subprocess, json

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
PAGES = {
    "medtronic_posting": "https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers/job/Heerlen-Limburg-Netherlands/Principal-Business-Performance-Analyst_R76374-1",
    "medtronic_nl_contact": "https://www.medtronic.com/nl-nl/about/contact-us.html",
    "medtronic_privacy": "https://www.medtronic.com/en-nl/about-us/privacy-statement.html",
    "hcl_job": "https://careers.hcltech.com/job/Senior-Technical-Lead/1367250555/",
    "hcl_careers_home": "https://careers.hcltech.com/",
    "hcl_contact": "https://www.hcltech.com/contact-us",
    "fh_careers": "https://fareharbor.com/careers/",
    "fh_jobs": "https://fareharbor.com/careers/jobs/",
    "fh_contact": "https://fareharbor.com/contact/",
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
for k, u in PAGES.items():
    h = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "30", u],
                       capture_output=True, text=True, timeout=45).stdout
    mails = sorted(set(EMAIL.findall(h)))
    mails = [m for m in mails if not re.search(r"\.(png|jpg|jpeg|svg|webp|gif|css|js)$", m, re.I)]
    mailtos = sorted(set(re.findall(r'mailto:([^"\'?&]+)', h)))
    print(f"== {k} len={len(h)}")
    print("   emails:", mails[:12])
    print("   mailto:", mailtos[:8])
