import urllib.request, urllib.error, re, json, sys

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9,nl;q=0.8"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BLOCK = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|css|js|woff|ico)$", re.I)

SITES = {
 "basic-fit": ["https://www.basic-fit.com/nl-nl/contact", "https://www.basic-fit.com/nl-nl/over-basic-fit/werken-bij-basic-fit",
               "https://careers.basic-fit.com/", "https://www.basic-fit.com/en-nl/contact"],
 "euronext": ["https://www.euronext.com/en/careers", "https://www.euronext.com/en/contact",
              "https://www.euronext.com/en/about/legal", "https://www.euronext.com/en/careers/working-at-euronext"],
 "salesforce": ["https://www.salesforce.com/company/careers/", "https://www.salesforce.com/company/contact/",
                "https://www.salesforce.com/company/legal/"],
 "jpmorgan": ["https://careers.jpmorgan.com/global/en/home", "https://www.jpmorganchase.com/contact-us",
              "https://www.jpmorganchase.com/about/our-business/recruitment-privacy"],
}
out = {}
for comp, urls in SITES.items():
    found = {}
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                html = r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"[{comp}] FAIL {u} {type(e).__name__} {str(e)[:80]}")
            continue
        addrs = set(a for a in EMAIL_RE.findall(html) if not BLOCK.search(a) and "sentry" not in a and "wixpress" not in a)
        for a in sorted(addrs):
            found.setdefault(a, u)
        print(f"[{comp}] {u} -> {sorted(addrs)[:8]} ({len(html)} bytes)")
    out[comp] = found
json.dump(out, open("/home/ubuntu/job-hunt-scratch/emails_found.json", "w"), indent=1)
print("=== SUMMARY ===")
for comp, f in out.items():
    for a, u in f.items():
        print(comp, "|", a, "| evidence:", u)
